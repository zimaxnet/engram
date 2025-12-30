import { useState } from 'react';
import { useAuth } from '../../auth';
import { LoginModal } from '../LoginModal/LoginModal';
import './UserMenu.css';

export function UserMenu() {
    const { isAuthenticated, isLoading, user, logout } = useAuth();
    const [showLoginModal, setShowLoginModal] = useState(false);

    if (isLoading) {
        return (
            <div className="user-menu-loading">
                <div className="spinner-small"></div>
            </div>
        );
    }

    if (isAuthenticated) {
        return (
            <div className="user-menu">
                <div className="user-info" title={user?.username}>
                    <span className="user-name">{user?.name || user?.username}</span>
                    <div className="user-avatar-active" onClick={logout}>
                        {user?.name?.[0] || '👤'}
                    </div>
                </div>
                <button className="logout-button" onClick={logout}>
                    Logout
                </button>
            </div>
        );
    }

    return (
        <>
            <div className="user-menu">
                <button className="login-button" onClick={() => setShowLoginModal(true)}>
                    Sign In
                </button>
            </div>
            <LoginModal
                isOpen={showLoginModal}
                onClose={() => setShowLoginModal(false)}
            />
        </>
    );
}
