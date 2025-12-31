# Authentication Setup Guide

## Overview

The EVALVision system uses **Supabase Auth** for user authentication. Users must be created in Supabase Auth (separate from the `people` table in the database).

## Creating Your First User

### Option 1: Via Supabase Dashboard (Recommended)

1. **Go to Supabase Dashboard**:
   - Visit: https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr
   - Navigate to **Authentication** → **Users**

2. **Create a New User**:
   - Click **"Add user"** or **"Invite user"**
   - Enter email: `ahelmy@eternityschooegypt.com` (or your email)
   - Enter password: Choose a secure password
   - **Important**: Add user metadata for role:
     ```json
     {
       "role": "ceo"
     }
     ```
   - Click **"Create user"**

3. **Set User Role** (in user metadata):
   - After creating user, click on the user
   - Go to **"Raw App Meta Data"** or **"Raw User Meta Data"**
   - Add:
     ```json
     {
       "role": "ceo"
     }
     ```
   - Or use one of: `ceo`, `pnc`, `department_head`, `staff`

### Option 2: Via Supabase SQL Editor

```sql
-- Create user via Supabase Auth (requires admin access)
-- Note: This uses Supabase's auth.users table, not the public.people table

-- You can also use the Supabase Dashboard to create users
-- Go to: Authentication → Users → Add user
```

### Option 3: Via Frontend Sign-Up (If Enabled)

If sign-up is enabled in Supabase settings:

1. Go to the login page
2. Click "Sign Up" (if available)
3. Enter your email and password
4. Check your email for confirmation link
5. After confirmation, an admin needs to set your role in Supabase Dashboard

## Test Users

### Recommended Test Accounts

Create these users in Supabase Dashboard:

#### 1. CEO Account
- **Email**: `ahelmy@eternityschooegypt.com`
- **Password**: (set your own)
- **Role**: `ceo`
- **Permissions**: Full access to everything

#### 2. P&C Account
- **Email**: `p.c@eternityschooegypt.com`
- **Password**: (set your own)
- **Role**: `pnc`
- **Permissions**: Staff management, eligibility checks

#### 3. Department Head Account
- **Email**: `principal@eternityschooegypt.com`
- **Password**: (set your own)
- **Role**: `department_head`
- **Permissions**: Nominate, vote, evaluate

#### 4. Staff Account
- **Email**: `teacher@eternityschooegypt.com`
- **Password**: (set your own)
- **Role**: `staff`
- **Permissions**: View own evaluations, self-evaluate

## Setting User Roles

### Via Supabase Dashboard

1. Go to **Authentication** → **Users**
2. Click on the user
3. Scroll to **"Raw App Meta Data"** or **"Raw User Meta Data"**
4. Add or edit:
   ```json
   {
     "role": "ceo"
   }
   ```
5. Save

### Via SQL (Admin Only)

```sql
-- Update user metadata (requires service_role)
UPDATE auth.users
SET raw_app_meta_data = jsonb_build_object('role', 'ceo')
WHERE email = 'ahelmy@eternityschooegypt.com';
```

## Role Hierarchy

- **ceo**: Highest level, full access
- **pnc**: People & Culture, staff management
- **department_head**: Can nominate, vote, evaluate
- **staff**: Basic access, view own data

## Password Reset

If you forget your password:

1. Go to login page
2. Click "Forgot password" (if implemented)
3. Or use Supabase Dashboard:
   - Go to **Authentication** → **Users**
   - Find your user
   - Click **"Reset password"**
   - Check email for reset link

## Troubleshooting

### "Invalid login credentials"
- Check email is correct
- Check password is correct
- Verify user exists in Supabase Auth (not just in `people` table)

### "User not found"
- User must be created in Supabase Auth
- Creating a record in `people` table is NOT enough
- Go to Supabase Dashboard → Authentication → Users

### "No role assigned"
- User needs `role` in metadata
- Set via Supabase Dashboard → Users → User → Raw App Meta Data

### "Permission denied"
- Check user role is set correctly
- Verify RLS policies allow access
- Check if user email matches in both `auth.users` and `people` table

## Quick Setup Script

For development, you can create a test user via Supabase Dashboard:

1. **Enable Email Auth** (if not already):
   - Supabase Dashboard → Authentication → Providers
   - Enable "Email" provider
   - Disable "Confirm email" for development (optional)

2. **Create Test User**:
   - Authentication → Users → Add user
   - Email: `test@eternityschooegypt.com`
   - Password: `Test123!@#` (or your choice)
   - Auto Confirm: ✅ (for development)
   - Set role in metadata: `{"role": "ceo"}`

3. **Login**:
   - Use the email and password you just created

## Security Notes

- **Never commit passwords to git**
- Use strong passwords in production
- Enable email confirmation in production
- Use environment variables for Supabase keys
- Rotate service role keys regularly

