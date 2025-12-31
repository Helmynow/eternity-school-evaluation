# EVALVision Frontend - Eternity School Evaluation System

Frontend application for the Employee of the Month (EOM) and Multi-Rater Evaluation (MRE) system.

## Features

- **EOM Nomination & Voting**: Submit and vote on Employee of the Month nominations across 5 categories
- **MRE Evaluations**: Complete 360-degree performance evaluations with role-based weight matrices
- **Real-time Dashboard**: Monitor participation, view bias reports, and track evaluation progress
- **Role-based Access**: Different interfaces for CEO, P&C, Department Heads, and Staff
- **ESE Brand Guidelines**: Full implementation of Eternity School brand colors, fonts, and mascots

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Environment Variables

Create a `.env` file:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

## Brand Guidelines

The frontend follows ESE brand guidelines:
- **Language Division**: Blue palette (#094773, #2D7EA1, etc.)
- **International Division**: Green palette (#2C5B4C, #7CA48A, etc.)
- **Fonts**: Plus Jakarta Sans (body), Fraunces (headings)
- **Mascots**: Located in `/public/assets/mascots/`
- **Icons**: Located in `/public/assets/icons/`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── dashboard/    # Dashboard components
│   │   ├── eom/          # EOM nomination & voting
│   │   ├── mre/          # MRE evaluation forms
│   │   ├── auth/          # Authentication
│   │   └── layout/        # Layout components
│   ├── lib/               # Utilities & API clients
│   ├── hooks/             # React hooks
│   └── styles/            # CSS & theme files
└── public/
    └── assets/            # Mascots, icons, media
```

