# Quick Guide: Create Your First Test User

## Step-by-Step Instructions

### 1. Access Supabase Dashboard

Visit: https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr/auth/users

### 2. Create a New User

1. Click **"Add user"** button (top right)
2. Fill in:
   - **Email**: `ahelmy@eternityschooegypt.com` (or your email)
   - **Password**: Choose a password (e.g., `Test123!@#`)
   - **Auto Confirm User**: ✅ (check this for development)
3. Click **"Create user"**

### 3. Set User Role

1. Click on the user you just created
2. Scroll down to **"Raw App Meta Data"**
3. Click **"Edit"**
4. Add this JSON:
   ```json
   {
     "role": "ceo"
   }
   ```
5. Click **"Save"**

### 4. Login to Frontend

1. Go to: http://localhost:3000
2. Enter your email and password
3. You should be logged in!

## Alternative: Use Supabase CLI

```bash
# Install Supabase CLI if not already
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref ywcfqlyhesnikclesgpr

# Create user via SQL (requires service role)
# Note: This is more complex, dashboard method is easier
```

## Test User Credentials (After Creation)

Once you create a user, you can use:

- **Email**: The email you created (e.g., `ahelmy@eternityschooegypt.com`)
- **Password**: The password you set

## Role Options

When setting the role in metadata, use one of:
- `ceo` - Full access
- `pnc` - People & Culture access
- `department_head` - Can nominate and vote
- `staff` - Basic access

