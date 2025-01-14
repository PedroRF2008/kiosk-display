import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from dotenv import load_dotenv

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get device key from env
        device_key = os.getenv("DEVICE_KEY")
        if not device_key:
            raise ValueError("DEVICE_KEY not found in environment variables")

        # Service account credentials
        cred_dict = {
            "type": "service_account",
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL"),
            "universe_domain": "googleapis.com"
        }
        
        # Firebase web config
        web_config = {
            "apiKey": os.getenv("FIREBASE_API_KEY"),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.getenv("FIREBASE_PROJECT_ID"),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.getenv("FIREBASE_APP_ID")
        }
        
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': web_config['storageBucket']
        })
        
        # Initialize Firestore and Storage
        db = firestore.client()
        bucket = storage.bucket()
        
        return db, bucket, device_key
    except Exception as e:
        print(f"Error initializing Firebase: {str(e)}")
        return None, None, None 