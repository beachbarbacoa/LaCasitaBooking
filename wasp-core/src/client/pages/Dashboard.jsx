import { useState } from 'react';
import { useAuth } from '@wasp/auth';
import { logout } from '@wasp/auth/actions';
import { useNavigate } from 'react-router-dom';
import QRScanner from '../components/QRScanner';

export default function Dashboard() {
  const { data: user, isLoading } = useAuth();
  const navigate = useNavigate();
  const [showScanner, setShowScanner] = useState(false);
  
  if (isLoading) return 'Loading...';
  if (!user) return 'Not authenticated';

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleScan = (data) => {
    // Extract business ID from scanned data
    let businessId = data;
    try {
      const url = new URL(data);
      const pathParts = url.pathname.split('/');
      if (pathParts.length >= 3 && pathParts[1] === 'business') {
        businessId = pathParts[2];
      }
    } catch (e) {
      // Not a URL, use raw data as business ID
    }
    
    console.log('Navigating to business:', businessId);
    navigate(`/business/${businessId}/reserve`);
    setShowScanner(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="absolute inset-0 bg-gradient-to-r from-cyan-400 to-light-blue-500 shadow-lg transform -skew-y-6 sm:skew-y-0 sm:-rotate-6 sm:rounded-3xl"></div>
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <h1 className="text-2xl font-bold mb-4">Welcome, Concierge!</h1>
          <p className="mb-6">You are logged in as: {user.email}</p>
          
          <div className="mb-6">
            <h2 className="text-xl font-semibold mb-2">Quick Actions</h2>
            <ul className="list-disc pl-5 mb-4">
              <li>Make a new reservation</li>
              <li>View your earnings</li>
              <li>Manage your profile</li>
            </ul>
            
            {showScanner ? (
              <div className="mt-4 p-4 border rounded-lg">
                <QRScanner onScan={handleScan} />
                <button
                  onClick={() => setShowScanner(false)}
                  className="mt-2 bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded"
                >
                  Cancel Scan
                </button>
              </div>
            ) : (
              <button
                onClick={() => setShowScanner(true)}
                className="mt-2 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              >
                Scan Business QR Code
              </button>
            )}
          </div>

          <button
            onClick={handleLogout}
            className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}