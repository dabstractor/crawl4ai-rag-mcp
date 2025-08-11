# PostgreSQL Database Connection Adapter
# This script creates a local PostgreSQL database connection that mimics Supabase interface

import os
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import json
from typing import Dict, List, Any, Optional, Union

class PostgreSQLAdapter:
    """Adapter to make PostgreSQL work like Supabase client"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
    
    def connect(self, timeout: int = 30):
        """Connect to PostgreSQL database with timeout"""
        if not self.connection or self.connection.closed:
            try:
                # Parse connection string to add timeout parameters
                import urllib.parse
                parsed = urllib.parse.urlparse(self.connection_string)
                # Add connection timeout parameters
                self.connection = psycopg2.connect(
                    self.connection_string,
                    cursor_factory=RealDictCursor,
                    connect_timeout=timeout
                )
            except psycopg2.OperationalError as e:
                raise Exception(f"Failed to connect to PostgreSQL database: {str(e)}")
            except Exception as e:
                raise Exception(f"Database connection error: {str(e)}")
        return self.connection
    
    def table(self, table_name: str):
        """Return a table interface"""
        return PostgreSQLTable(self, table_name)
    
    def rpc(self, function_name: str, params: Dict[str, Any]):
        """Execute a stored procedure/function"""
        return PostgreSQLRPC(self, function_name, params)

class PostgreSQLRPC:
    """Handle RPC (stored procedure) calls"""
    
    def __init__(self, adapter: PostgreSQLAdapter, function_name: str, params: Dict[str, Any]):
        self.adapter = adapter
        self.function_name = function_name
        self.params = params
    
    def execute(self, timeout: int = 30):
        """Execute the RPC call with timeout"""
        try:
            conn = self.adapter.connect(timeout)
            cur = conn.cursor()
            
            # Set statement timeout
            cur.execute(f"SET LOCAL statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            if self.function_name == "match_crawled_pages":
                # Handle vector similarity search for crawled pages
                query_embedding = self.params.get('query_embedding', [])
                match_count = self.params.get('match_count', 10)
                source_filter = self.params.get('source_filter')
                
                # Build the query
                base_query = """
                SELECT url, chunk_number, content, metadata, source_id,
                       1 - (embedding <=> %s::vector) as similarity
                FROM crawled_pages
                """
                
                query_params = [json.dumps(query_embedding)]
                where_conditions = []
                
                if source_filter:
                    where_conditions.append("source_id = %s")
                    query_params.append(source_filter)
                
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                base_query += " ORDER BY similarity DESC LIMIT %s"
                query_params.append(match_count)
                
                cur.execute(base_query, query_params)
                
            elif self.function_name == "match_code_examples":
                # Handle vector similarity search for code examples
                query_embedding = self.params.get('query_embedding', [])
                match_count = self.params.get('match_count', 10)
                source_filter = self.params.get('source_filter')
                
                base_query = """
                SELECT url, chunk_number, content, summary, metadata, source_id,
                       1 - (embedding <=> %s::vector) as similarity
                FROM code_examples
                """
                
                query_params = [json.dumps(query_embedding)]
                where_conditions = []
                
                if source_filter:
                    where_conditions.append("source_id = %s")
                    query_params.append(source_filter)
                
                if where_conditions:
                    base_query += " WHERE " + " AND ".join(where_conditions)
                
                base_query += " ORDER BY similarity DESC LIMIT %s"
                query_params.append(match_count)
                
                cur.execute(base_query, query_params)
            else:
                # Generic RPC call
                param_placeholders = ', '.join(['%s'] * len(self.params))
                query = f"SELECT * FROM {self.function_name}({param_placeholders})"
                cur.execute(query, list(self.params.values()))
            
            results = cur.fetchall()
            cur.close()
            
            return {"data": [dict(row) for row in results], "error": None}
            
        except psycopg2.OperationalError as e:
            if 'cur' in locals() and cur:
                cur.close()
            if 'timeout' in str(e).lower():
                return {"data": [], "error": f"RPC operation timed out after {timeout} seconds"}
            return {"data": [], "error": f"Database operational error during RPC: {str(e)}"}
        except Exception as e:
            if 'cur' in locals() and cur:
                cur.close()
            return {"data": [], "error": f"RPC operation failed: {str(e)}"}
        finally:
            if 'cur' in locals() and cur:
                cur.close()

class PostgreSQLTable:
    """Table interface that mimics Supabase table operations"""
    
    def __init__(self, adapter: PostgreSQLAdapter, table_name: str):
        self.adapter = adapter
        self.table_name = table_name
        self._select_columns = "*"
        self._where_conditions = []
        self._values = []
        self._limit_value = None
        self._order_by = None
    
    def select(self, columns: str = "*"):
        """Select columns"""
        self._select_columns = columns
        return self
    
    def eq(self, column: str, value: Any):
        """Add equality condition"""
        self._where_conditions.append(f"{column} = %s")
        self._values.append(value)
        return self
    
    def in_(self, column: str, values: List[Any]):
        """Add IN condition"""
        placeholders = ', '.join(['%s'] * len(values))
        self._where_conditions.append(f"{column} IN ({placeholders})")
        self._values.extend(values)
        return self
    
    def limit(self, count: int):
        """Limit results"""
        self._limit_value = count
        return self
    
    def order(self, column: str, desc: bool = False):
        """Order results"""
        direction = "DESC" if desc else "ASC"
        self._order_by = f"{column} {direction}"
        return self
    
    def execute(self, timeout: int = 30):
        """Execute the query and return results with timeout"""
        try:
            conn = self.adapter.connect(timeout)
            cur = conn.cursor()
            
            # Set statement timeout
            cur.execute(f"SET LOCAL statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            # Build query
            query_parts = [f"SELECT {self._select_columns} FROM {self.table_name}"]
            
            if self._where_conditions:
                query_parts.append(f"WHERE {' AND '.join(self._where_conditions)}")
            
            if self._order_by:
                query_parts.append(f"ORDER BY {self._order_by}")
            
            if self._limit_value:
                query_parts.append(f"LIMIT {self._limit_value}")
            
            query = " ".join(query_parts)
            
            cur.execute(query, self._values)
            results = cur.fetchall()
            cur.close()
            
            # Convert to list of dicts (like Supabase format)
            return {"data": [dict(row) for row in results], "error": None}
        except psycopg2.OperationalError as e:
            if 'timeout' in str(e).lower():
                return {"data": [], "error": f"Query timed out after {timeout} seconds"}
            return {"data": [], "error": f"Database operational error: {str(e)}"}
        except Exception as e:
            return {"data": [], "error": f"Query execution error: {str(e)}"}
    
    def insert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], timeout: int = 30):
        """Insert data (single record or batch) with timeout"""
        try:
            conn = self.adapter.connect(timeout)
            cur = conn.cursor()
            
            # Set statement timeout
            cur.execute(f"SET LOCAL statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            # Handle both single records and batch inserts
            if isinstance(data, dict):
                data = [data]
            
            if not data:
                return {"data": [], "error": None}
            
            # Prepare the data for insertion
            sample_record = data[0]
            columns = list(sample_record.keys())
            
            # Handle JSON fields properly
            processed_data = []
            for record in data:
                processed_record = []
                for col in columns:
                    value = record.get(col)
                    # Convert Python dicts/lists to PostgreSQL JSON
                    if isinstance(value, (dict, list)):
                        processed_record.append(Json(value))
                    else:
                        processed_record.append(value)
                processed_data.append(processed_record)
            
            # Build the INSERT query
            placeholders = ', '.join(['%s'] * len(columns))
            query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)}) 
            VALUES ({placeholders})
            RETURNING *
            """
            
            results = []
            for record_data in processed_data:
                cur.execute(query, record_data)
                result = cur.fetchone()
                if result:
                    results.append(dict(result))
            
            conn.commit()
            cur.close()
            
            return {"data": results, "error": None}
            
        except psycopg2.OperationalError as e:
            if conn:
                conn.rollback()
            if 'timeout' in str(e).lower():
                return {"data": [], "error": f"Insert operation timed out after {timeout} seconds"}
            return {"data": [], "error": f"Database operational error during insert: {str(e)}"}
        except Exception as e:
            if conn:
                conn.rollback()
            return {"data": [], "error": f"Insert operation failed: {str(e)}"}
        finally:
            if 'cur' in locals() and cur:
                cur.close()
    
    def upsert(self, data: Union[Dict[str, Any], List[Dict[str, Any]]], timeout: int = 30):
        """Upsert data (for now, just insert - can be enhanced later) with timeout"""
        return self.insert(data, timeout)
    
    def delete(self, timeout: int = 30):
        """Delete records matching the conditions with timeout"""
        try:
            conn = self.adapter.connect(timeout)
            cur = conn.cursor()
            
            # Set statement timeout
            cur.execute(f"SET LOCAL statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            if not self._where_conditions:
                raise ValueError("DELETE requires WHERE conditions for safety")
            
            query = f"DELETE FROM {self.table_name} WHERE {' AND '.join(self._where_conditions)}"
            cur.execute(query, self._values)
            conn.commit()
            cur.close()
            
            return {"data": [], "error": None}
            
        except psycopg2.OperationalError as e:
            if conn:
                conn.rollback()
            if 'timeout' in str(e).lower():
                return {"data": [], "error": f"Delete operation timed out after {timeout} seconds"}
            return {"data": [], "error": f"Database operational error during delete: {str(e)}"}
        except Exception as e:
            if conn:
                conn.rollback()
            return {"data": [], "error": f"Delete operation failed: {str(e)}"}
        finally:
            if 'cur' in locals() and cur:
                cur.close()
    
    def update(self, updates: Dict[str, Any], timeout: int = 30):
        """Update records with timeout"""
        try:
            conn = self.adapter.connect(timeout)
            cur = conn.cursor()
            
            # Set statement timeout
            cur.execute(f"SET LOCAL statement_timeout = {timeout * 1000}")  # Convert to milliseconds
            
            if not self._where_conditions:
                raise ValueError("UPDATE requires WHERE conditions for safety")
            
            # Build SET clause
            set_clauses = []
            update_values = []
            for col, val in updates.items():
                set_clauses.append(f"{col} = %s")
                if isinstance(val, (dict, list)):
                    update_values.append(Json(val))
                else:
                    update_values.append(val)
            
            query = f"""
            UPDATE {self.table_name} 
            SET {', '.join(set_clauses)}
            WHERE {' AND '.join(self._where_conditions)}
            RETURNING *
            """
            
            all_values = update_values + self._values
            cur.execute(query, all_values)
            results = cur.fetchall()
            conn.commit()
            cur.close()
            
            return {"data": [dict(row) for row in results], "error": None}
            
        except psycopg2.OperationalError as e:
            if conn:
                conn.rollback()
            if 'timeout' in str(e).lower():
                return {"data": [], "error": f"Update operation timed out after {timeout} seconds"}
            return {"data": [], "error": f"Database operational error during update: {str(e)}"}
        except Exception as e:
            if conn:
                conn.rollback()
            return {"data": [], "error": f"Update operation failed: {str(e)}"}
        finally:
            if 'cur' in locals() and cur:
                cur.close()

def get_postgresql_client() -> PostgreSQLAdapter:
    """Get a PostgreSQL client adapter"""
    connection_string = os.getenv("SUPABASE_URL")  # We'll reuse this env var
    if not connection_string:
        raise ValueError("SUPABASE_URL must be set for PostgreSQL connection")
    
    return PostgreSQLAdapter(connection_string)
