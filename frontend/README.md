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

# Copy environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

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
- **Logo**: Located in `/public/assets/media/logo-no-bound.png`

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
│   ├── hooks/             # React hooks (useAuth, useAPI)
│   ├── lib/               # Utilities & API clients
│   └── styles/            # CSS & theme files
└── public/
    └── assets/            # Mascots, icons, media
```

## Development

The app runs on `http://localhost:3000` and proxies API requests to `http://localhost:8000`.

### Key Technologies

- **React 18.3** - UI framework
- **Vite 5.4** - Build tool
- **React Router 6.26** - Routing
- **Tailwind CSS 3.4** - Styling
- **Supabase Auth** - Authentication
- **Axios** - HTTP client
- **Recharts** - Data visualization
- **React Hot Toast** - Notifications

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
