# Deployment Guide

This guide covers deploying the Eternity School Evaluation System frontend application.

## Prerequisites

- Node.js 18+ and npm
- Environment variables configured
- Backend API running and accessible
- Supabase project configured

## Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=http://localhost:8000
```

For production:
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_URL=https://api.yourdomain.com
```

## Development Build

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173` (or the port Vite assigns).

## Production Build

### 1. Build the Application

```bash
cd frontend
npm install
npm run build
```

This creates an optimized production build in the `dist/` directory.

### 2. Test Production Build Locally

```bash
npm run preview
```

### 3. Deploy to Static Hosting

#### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow prompts to configure project
4. Add environment variables in Vercel dashboard

#### Netlify

1. Install Netlify CLI: `npm i -g netlify-cli`
2. Run: `netlify deploy --prod`
3. Configure environment variables in Netlify dashboard

#### Traditional Web Server

1. Copy `dist/` contents to web server root
2. Configure server to serve `index.html` for all routes (SPA routing)
3. Set up environment variables on server

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    root /var/www/eternity-eval-frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (if needed)
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Post-Deployment Checklist

- [ ] Verify environment variables are set
- [ ] Test authentication flow
- [ ] Verify API connectivity
- [ ] Test all major features
- [ ] Check error boundaries work
- [ ] Verify loading states display
- [ ] Test on multiple browsers
- [ ] Check mobile responsiveness
- [ ] Verify CORS settings
- [ ] Test with different user roles

## Troubleshooting

### CORS Errors
- Verify backend CORS settings allow your frontend domain
- Check `VITE_API_URL` is correct

### Authentication Issues
- Verify Supabase credentials
- Check Supabase RLS policies
- Verify JWT token handling

### API Connection Issues
- Verify backend is running
- Check `VITE_API_URL` points to correct backend
- Verify network connectivity
- Check backend logs for errors

### Build Errors
- Clear `node_modules` and reinstall
- Check Node.js version (18+)
- Verify all dependencies are installed
- Check for TypeScript errors (if using TS)

## Performance Optimization

### Already Implemented
- Code splitting via React Router
- Lazy loading for routes
- Optimized bundle size
- Loading skeletons for better UX

### Additional Optimizations
- Enable gzip compression on server
- Use CDN for static assets
- Implement service worker for caching
- Add image optimization
- Enable HTTP/2

## Security Considerations

1. **Environment Variables**: Never commit `.env` files
2. **API Keys**: Use environment variables, not hardcoded values
3. **Authentication**: Always verify user authentication
4. **Authorization**: Check user roles before showing admin features
5. **HTTPS**: Always use HTTPS in production
6. **CSP Headers**: Configure Content Security Policy
7. **XSS Protection**: React automatically escapes, but be careful with `dangerouslySetInnerHTML`

## Monitoring

### Recommended Tools
- **Error Tracking**: Sentry, LogRocket
- **Analytics**: Google Analytics, Plausible
- **Performance**: Lighthouse, WebPageTest
- **Uptime**: UptimeRobot, Pingdom

### Key Metrics to Monitor
- Page load times
- API response times
- Error rates
- User authentication success rate
- Feature usage

## Rollback Procedure

1. Keep previous build artifacts
2. Revert to previous deployment
3. Clear CDN cache if applicable
4. Verify rollback was successful
5. Investigate issues in staging environment

## Continuous Deployment

### GitHub Actions Example

```yaml
name: Deploy Frontend

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npm run build
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
```

## Support

For deployment issues, check:
1. Backend API logs
2. Browser console errors
3. Network tab in DevTools
4. Supabase dashboard logs
5. Server logs (if self-hosted)
