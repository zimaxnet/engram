import { useAuth } from '../../auth';
import './UserMenu.css';

export function UserMenu() {
    const { isAuthenticated, isLoading, user, login, logout } = useAuth();

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
        <div className="user-menu">
            <button className="login-button" onClick={login}>
                Sign In
            </button>
        </div>
    );
}
