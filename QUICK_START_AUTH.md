# Quick Start: Authentication

## You Need to Create a User First!

The system uses Supabase Auth. You need to create a user before you can log in.

### Fastest Way (2 minutes):

1. **Go to Supabase Dashboard**:
   https://supabase.com/dashboard/project/ywcfqlyhesnikclesgpr/auth/users

2. **Click "Add user"**:
   - Email: `test@eternityschooegypt.com`
   - Password: `Test123!@#` (or your choice)
   - ✅ Check "Auto Confirm User"
   - Click "Create user"

3. **Set Role** (click on the user you just created):
   - Scroll to "Raw App Meta Data"
   - Click "Edit"
   - Add: `{"role": "ceo"}`
   - Save

4. **Login**:
   - Go to: http://localhost:3000
   - Email: `test@eternityschooegypt.com`
   - Password: `Test123!@#`

That's it! You're in! 🎉

## Need Help?

See `docs/AUTHENTICATION_SETUP.md` for detailed instructions.
