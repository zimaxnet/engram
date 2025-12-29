import asyncio
import logging
import os
from dotenv import load_dotenv

# Load env before importing backend
load_dotenv()

from backend.api.middleware.auth import EntraIDAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_auth_config():
    logger.info("Starting Auth Configuration Verification...")
    
    # Check Env Vars
    tenant_id = os.environ.get("AZURE_AD_TENANT_ID")
    external_id = os.environ.get("AZURE_AD_EXTERNAL_ID")
    external_domain = os.environ.get("AZURE_AD_EXTERNAL_DOMAIN")
    
    logger.info(f"Environment Config:")
    logger.info(f"  AZURE_AD_TENANT_ID: {tenant_id}")
    logger.info(f"  AZURE_AD_EXTERNAL_ID: {external_id}")
    logger.info(f"  AZURE_AD_EXTERNAL_DOMAIN: {external_domain}")
    
    auth = EntraIDAuth()
    
    logger.info(f"EntraIDAuth Computed Properties:")
    logger.info(f"  Authority: {auth.authority}")
    logger.info(f"  JWKS URI: {auth.jwks_uri}")
    logger.info(f"  Issuer: {auth.issuer}")
    
    # Verify JWKS Connectivity
    logger.info(f"Attempting to fetch JWKS from {auth.jwks_uri}...")
    try:
        jwks = await auth.get_jwks()
        logger.info("✅ JWKS fetched successfully!")
        logger.info(f"  Key Count: {len(jwks.get('keys', []))}")
        keys = jwks.get('keys', [])
        if keys:
            logger.info(f"  First Key ID (kid): {keys[0].get('kid')}")
    except Exception as e:
        logger.error(f"❌ Failed to fetch JWKS: {e}")
        logger.error("Please check if the tenant domain and ID are correct and accessible.")

if __name__ == "__main__":
    asyncio.run(verify_auth_config())
