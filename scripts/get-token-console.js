// Copy and paste this entire script into your browser console (F12 > Console)
// while logged into https://engram.work

(async function() {
  try {
    // Get MSAL instance (adjust if your app uses a different variable)
    const msalInstance = window.msalInstance || window.msal;
    
    if (!msalInstance) {
      console.error('❌ MSAL instance not found. Make sure you are on the Engram app page.');
      return;
    }
    
    // Get all accounts
    const accounts = msalInstance.getAllAccounts();
    
    if (accounts.length === 0) {
      console.error('❌ No accounts found. Please log in first.');
      return;
    }
    
    const account = accounts[0];
    console.log('✅ Account found:', account.username);
    console.log('📋 Account ID:', account.homeAccountId);
    
    // Request access token with the API scope
    const CLIENT_ID = 'e32c6c40-615e-4a25-bc9e-944169e99697';
    const request = {
      scopes: [`api://${CLIENT_ID}/user_impersonation`],
      account: account
    };
    
    console.log('🔄 Requesting access token...');
    const response = await msalInstance.acquireTokenSilent(request);
    
    console.log('\n' + '='.repeat(70));
    console.log('✅ ACCESS TOKEN RECEIVED');
    console.log('='.repeat(70));
    console.log('\n📋 Copy this token for testing:');
    console.log(response.accessToken);
    console.log('\n💡 Test with:');
    console.log(`python3 scripts/test-chat-debug.py --token "${response.accessToken}" --message "hi"`);
    console.log('\n' + '='.repeat(70));
    
    // Also copy to clipboard if possible
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(response.accessToken);
      console.log('✅ Token copied to clipboard!');
    }
    
  } catch (error) {
    console.error('❌ Error getting token:', error);
    console.log('\n💡 If silent token acquisition failed, try:');
    console.log('   1. Refresh the page and log in again');
    console.log('   2. Check Network tab for the Authorization header');
    console.log('   3. Check Application > Local Storage for MSAL tokens');
  }
})();

