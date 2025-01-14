# -*- coding: utf-8 -*-

import cx_Oracle
import os
import sys

def initialize_oracle():
    """Initialize Oracle client with proper encoding settings"""
    try:
        # Set Oracle environment variables
        os.environ["NLS_LANG"] = "AMERICAN_AMERICA.AL32UTF8"
        
        # Determine the correct Oracle Client path based on the system
        if sys.platform.startswith("win"):
            oracle_client_path = r"C:\oracle\instantclient_19_25"
        else:
            oracle_client_path = "/opt/oracle/instantclient_19_10"
            
        # Initialize Oracle client with explicit path
        cx_Oracle.init_oracle_client(lib_dir=oracle_client_path)
        
        print(f"Oracle Client initialized with path: {oracle_client_path}")
        
        # Test connection
        dsn = cx_Oracle.makedsn('192.168.50.25', 1521, service_name='dic4')
        with cx_Oracle.connect(user='NCS', password='ncsdgt2025', dsn=dsn, encoding="UTF-8", nencoding="UTF-8") as connection:
            print("Oracle connection successful")
            
    except Exception as e:
        print(f"Error initializing Oracle: {str(e)}")
        print(f"Current ORACLE_HOME: {os.environ.get('ORACLE_HOME', 'Not set')}")
        print(f"Current LD_LIBRARY_PATH: {os.environ.get('LD_LIBRARY_PATH', 'Not set')}")
        print(f"Current PATH: {os.environ.get('PATH', 'Not set')}")
        print(f"Checking if directory exists: {os.path.exists(oracle_client_path)}")
        if os.path.exists(oracle_client_path):
            print(f"Contents of {oracle_client_path}:")
            print(os.listdir(oracle_client_path))
        raise