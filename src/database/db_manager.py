import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class DatabaseManager:
    def __init__(self, db_path: str = 'data/bot_database.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_database()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                email TEXT,
                address TEXT,
                location TEXT,
                referrer_id INTEGER,
                referral_code TEXT UNIQUE,
                referral_balance REAL DEFAULT 0.0,
                referral_joins INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users (user_id)
            )
        ''')
        
        # Add email column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
        except sqlite3.OperationalError:
            pass
            
        # Add location column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN location TEXT')
        except sqlite3.OperationalError:
            pass

        # Add referral fields to users table if they don't exist
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referrer_id INTEGER')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referral_code TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referral_balance REAL DEFAULT 0.0')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN referral_joins INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

        try:
            cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_referral_code ON users (referral_code)')
        except sqlite3.OperationalError:
            pass

        # Orders table (now for deals)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                hours INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                scheduled_date TEXT,
                preferred_time TEXT,
                notes TEXT,
                estimated_price REAL,
                final_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Deals table for negotiation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deals (
                deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                proposed_price REAL,
                proposed_by TEXT NOT NULL, -- 'user' or 'admin'
                message TEXT,
                status TEXT DEFAULT 'pending', -- 'pending', 'accepted', 'countered', 'rejected'
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        ''')
        
        # Add new columns to orders table if they don't exist
        try:
            cursor.execute('ALTER TABLE orders ADD COLUMN preferred_time TEXT')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE orders ADD COLUMN estimated_price REAL')
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute('ALTER TABLE orders ADD COLUMN final_price REAL')
        except sqlite3.OperationalError:
            pass

        # Subscriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                subscription_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_type TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Cart items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart_items (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                service_type TEXT NOT NULL,
                hours INTEGER NOT NULL,
                estimated_price REAL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Referral earnings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_earnings (
                earning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                referred_user_id INTEGER NOT NULL,
                order_id INTEGER,
                deal_price REAL NOT NULL,
                reward_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                FOREIGN KEY (referred_user_id) REFERENCES users (user_id),
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        ''')

        conn.commit()
        conn.close()

    # User Operations
    def add_or_update_user(self, user_id: int, username: str = None, first_name: str = None, 
                          last_name: str = None, phone_number: str = None, email: str = None, 
                          address: str = None, location: str = None, referrer_id: int = None) -> int:
        """Add or update a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute('''
                UPDATE users 
                SET username = COALESCE(?, username),
                    first_name = COALESCE(?, first_name),
                    last_name = COALESCE(?, last_name),
                    phone_number = COALESCE(?, phone_number),
                    email = COALESCE(?, email),
                    address = COALESCE(?, address),
                    location = COALESCE(?, location),
                    referrer_id = CASE WHEN ? IS NOT NULL AND referrer_id IS NULL THEN ? ELSE referrer_id END,
                    referral_code = COALESCE(referral_code, ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (username, first_name, last_name, phone_number, email, address, location, referrer_id, referrer_id, f'ref{user_id}', user_id))
        else:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name, last_name, phone_number, email, address, location, referrer_id, referral_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, phone_number, email, address, location, referrer_id, f'ref{user_id}'))

        conn.commit()
        conn.close()
        return user_id

    def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Get a user by their referral code"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE referral_code = ?', (referral_code,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def increment_referral_joins(self, referrer_id: int) -> bool:
        """Increment referral join count for a referrer"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE users
            SET referral_joins = COALESCE(referral_joins, 0) + 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (referrer_id,))

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def add_referral_earning(self, referrer_id: int, referred_user_id: int, order_id: int, deal_price: float, percentage: float = 0.2) -> Optional[float]:
        """Add referral earning for a referrer"""
        if not referrer_id or deal_price <= 0:
            return None

        reward = round(deal_price * percentage, 2)
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO referral_earnings (user_id, referred_user_id, order_id, deal_price, reward_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (referrer_id, referred_user_id, order_id, deal_price, reward))

        cursor.execute('''
            UPDATE users
            SET referral_balance = COALESCE(referral_balance, 0.0) + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (reward, referrer_id))

        conn.commit()
        conn.close()
        return reward

    def set_referral_balance(self, user_id: int, amount: float) -> bool:
        """Set a user's referral balance"""
        import logging
        logger = logging.getLogger(__name__)

        conn = self.get_connection()
        cursor = conn.cursor()

        logger.info(f"set_referral_balance: user_id={user_id}, amount={amount}")

        cursor.execute('''
            UPDATE users
            SET referral_balance = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (amount, user_id))

        conn.commit()
        rowcount = cursor.rowcount
        logger.info(f"set_referral_balance: rowcount={rowcount}")

        # Verify the update by querying the user
        cursor.execute('SELECT referral_balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if result:
            actual_balance = result[0]
            logger.info(f"set_referral_balance: verified balance={actual_balance}")
            success = actual_balance == amount
        else:
            logger.warning(f"set_referral_balance: user {user_id} not found after update")
            success = False

        conn.close()
        return success

    def get_referral_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Return referral details for a user"""
        user = self.get_user(user_id)
        if not user:
            return None

        return {
            'referrer_id': user.get('referrer_id'),
            'referral_code': user.get('referral_code'),
            'referral_balance': user.get('referral_balance') or 0.0,
            'referral_joins': user.get('referral_joins') or 0
        }

    def get_detailed_referral_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed referral statistics for a user"""
        user = self.get_user(user_id)
        if not user:
            return None

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get total earnings and number of deals
        cursor.execute('''
            SELECT 
                COUNT(*) as total_deals,
                COALESCE(SUM(reward_amount), 0) as total_earnings,
                COALESCE(SUM(deal_price), 0) as total_deal_value
            FROM referral_earnings 
            WHERE user_id = ?
        ''', (user_id,))
        
        earnings_row = cursor.fetchone()
        
        conn.close()

        return {
            'user_id': user_id,
            'username': user.get('username'),
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'phone_number': user.get('phone_number'),
            'email': user.get('email'),
            'referral_code': user.get('referral_code'),
            'referral_balance': user.get('referral_balance') or 0.0,
            'referral_joins': user.get('referral_joins') or 0,
            'total_deals': earnings_row['total_deals'] if earnings_row else 0,
            'total_earnings': earnings_row['total_earnings'] if earnings_row else 0.0,
            'total_deal_value': earnings_row['total_deal_value'] if earnings_row else 0.0,
            'created_at': user.get('created_at')
        }

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    # Order Operations
    def create_order(self, user_id: int, service_type: str, hours: int, 
                    scheduled_date: str = None, notes: str = None) -> int:
        """Create a new order"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (user_id, service_type, hours, scheduled_date, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, service_type, hours, scheduled_date, notes))
        
        conn.commit()
        order_id = cursor.lastrowid
        conn.close()
        return order_id

    def create_deal(self, order_id: int, proposed_price: float, proposed_by: str, message: str = None) -> int:
        """Create a new deal proposal"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO deals (order_id, proposed_price, proposed_by, message)
            VALUES (?, ?, ?, ?)
        ''', (order_id, proposed_price, proposed_by, message))
        
        conn.commit()
        deal_id = cursor.lastrowid
        conn.close()
        return deal_id

    def get_latest_deal(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get the latest deal for an order"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM deals 
            WHERE order_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        ''', (order_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def update_deal_status(self, deal_id: int, status: str) -> bool:
        """Update deal status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE deals 
            SET status = ?
            WHERE deal_id = ?
        ''', (status, deal_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def get_order_with_deals(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order with all its deals"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM orders WHERE order_id = ?', (order_id,))
        order_row = cursor.fetchone()
        
        if not order_row:
            conn.close()
            return None
        
        cursor.execute('''
            SELECT * FROM deals 
            WHERE order_id = ? 
            ORDER BY created_at DESC
        ''', (order_id,))
        
        deal_rows = cursor.fetchall()
        conn.close()
        
        order_dict = dict(order_row)
        order_dict['deals'] = [dict(row) for row in deal_rows]
        return order_dict

    def get_user_orders(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's orders"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        orders = []
        for row in rows:
            order_dict = dict(row)
            orders.append(order_dict)
        
        return orders

    def update_order_status(self, order_id: int, status: str, final_price: float = None) -> bool:
        """Update order status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE orders 
            SET status = ?, final_price = COALESCE(?, final_price), updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        ''', (status, final_price, order_id))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
    def update_order_time(self, order_id: int, preferred_time: str) -> bool:
        """Update order preferred time"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE orders 
            SET preferred_time = ?, updated_at = CURRENT_TIMESTAMP
            WHERE order_id = ?
        ''', (preferred_time, order_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    # Cart Operations
    def add_to_cart(self, user_id: int, service_type: str, hours: int, estimated_price: float) -> int:
        """Add item to cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cart_items (user_id, service_type, hours, estimated_price)
            VALUES (?, ?, ?, ?)
        ''', (user_id, service_type, hours, estimated_price))
        
        conn.commit()
        cart_id = cursor.lastrowid
        conn.close()
        return cart_id

    def get_cart(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's cart items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM cart_items WHERE user_id = ? ORDER BY added_at ASC', (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

    def clear_cart(self, user_id: int) -> bool:
        """Clear user's cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    def remove_from_cart(self, cart_id: int) -> bool:
        """Remove item from cart"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cart_items WHERE cart_id = ?', (cart_id,))
        
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0

    # Subscription Operations
    def add_subscription(self, user_id: int, plan_type: str) -> int:
        """Add subscription for user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO subscriptions (user_id, plan_type, start_date)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, plan_type))
        
        conn.commit()
        subscription_id = cursor.lastrowid
        conn.close()
        return subscription_id

    def get_user_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's active subscription"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM subscriptions 
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

    def cancel_subscription(self, subscription_id: int) -> bool:
        """Cancel subscription"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE subscriptions
            SET status = 'cancelled', end_date = CURRENT_TIMESTAMP
            WHERE subscription_id = ?
        ''', (subscription_id,))

        conn.commit()
        affected = cursor.rowcount
        conn.close()
        return affected > 0
