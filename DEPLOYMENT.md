# Deployment Guide

This guide covers deploying Slitherin to GitHub Pages and other hosting platforms.

## GitHub Pages Deployment

GitHub Pages is the easiest way to host the web version of Slitherin for free.

### Step 1: Enable GitHub Pages

1. Go to your GitHub repository
2. Click **Settings** (top-right)
3. Scroll down to **Pages** in the left sidebar
4. Under **Source**, select:
   - **Branch**: Select your branch (e.g., `main` or your current branch)
   - **Folder**: Select `/docs`
5. Click **Save**

GitHub will automatically deploy your site to:
```
https://<username>.github.io/<repository>/
```

For example: `https://vonalphabiszulu.github.io/slitherin/`

### Step 2: Wait for Deployment

- GitHub Pages typically takes 1-3 minutes to deploy
- You'll see a green checkmark when deployment is complete
- Visit your site URL to verify it's working

### Step 3: Update Repository Settings (Optional)

1. Add the GitHub Pages URL to your repository description
2. In **Settings → General**, add:
   - **Website**: `https://<username>.github.io/<repository>/`
   - **Topics**: `snake-game`, `ai`, `python`, `javascript`, `github-pages`

### Troubleshooting

**Issue: 404 Not Found**
- Ensure `/docs` folder exists in your selected branch
- Check that `index.html` is in `/docs/index.html`
- Wait a few minutes for deployment to complete

**Issue: Styles not loading**
- Ensure `.nojekyll` file exists in `/docs/`
- Check that CSS/JS paths are relative (not absolute)
- Clear browser cache and reload

**Issue: JavaScript errors**
- Open browser DevTools (F12) to see console errors
- Check that all `.js` files are in `/docs/js/`
- Verify file paths are case-sensitive correct

### Custom Domain (Optional)

To use a custom domain:

1. Add a file `/docs/CNAME` with your domain:
   ```
   slitherin.yourdomain.com
   ```

2. Configure DNS at your domain provider:
   - Add a `CNAME` record pointing to `<username>.github.io`

3. In GitHub Settings → Pages, enter your custom domain

4. Enable **Enforce HTTPS** (recommended)

## Alternative Hosting Options

### Netlify

Netlify offers easy deployment with automatic builds:

1. Sign up at [netlify.com](https://www.netlify.com)
2. Click **Add new site → Import an existing project**
3. Connect your GitHub repository
4. Configure build settings:
   - **Base directory**: `docs`
   - **Build command**: (leave empty - static site)
   - **Publish directory**: `.` (current directory)
5. Click **Deploy site**

Benefits:
- Automatic deployments on git push
- Preview deployments for pull requests
- Easy custom domain setup
- Better performance than GitHub Pages

### Vercel

Similar to Netlify with excellent performance:

1. Sign up at [vercel.com](https://vercel.com)
2. Click **Add New → Project**
3. Import your GitHub repository
4. Configure:
   - **Root Directory**: `docs`
   - **Framework Preset**: Other
5. Click **Deploy**

### Self-Hosted

Any static file server works:

**Python:**
```bash
cd docs
python3 -m http.server 8000
```

**Node.js:**
```bash
cd docs
npx serve
```

**Nginx:**
```nginx
server {
    listen 80;
    server_name slitherin.example.com;
    root /path/to/slitherin/docs;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

**Apache:**
```apache
<VirtualHost *:80>
    ServerName slitherin.example.com
    DocumentRoot /path/to/slitherin/docs

    <Directory /path/to/slitherin/docs>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

## Python Backend Deployment (Future)

If you want to run the Python MILP solver server-side:

### Option 1: Flask API + Static Frontend

1. Create Flask API that wraps MILP solver
2. Deploy API to Heroku/Railway/Render
3. Keep static frontend on GitHub Pages
4. Frontend calls API via CORS-enabled endpoints

### Option 2: Full Python Deployment

Deploy entire Python app to:
- **Heroku**: `heroku create` + `git push heroku main`
- **Railway**: Connect GitHub repo, auto-deploy
- **Google Cloud Run**: Containerize with Docker
- **AWS Elastic Beanstalk**: Python application environment

### Option 3: WebAssembly MILP (Advanced)

Compile SCIP solver to WebAssembly:
1. Build SCIP with Emscripten
2. Create JavaScript bindings
3. Run true MILP in browser (no server needed!)

This is complex but would enable full MILP solver client-side.

## Performance Optimization

### For GitHub Pages

1. **Minify Files**:
   ```bash
   # Install terser for JS minification
   npm install -g terser

   # Minify JavaScript
   cd docs/js
   for file in *.js; do
       terser "$file" -o "${file%.js}.min.js" -c -m
   done
   ```

2. **Compress Assets**:
   - Use smaller images (PNG → WebP)
   - Compress CSS with cssnano
   - Enable gzip in server config

3. **CDN (optional)**:
   - Use jsDelivr CDN for library files
   - Cache static assets aggressively

### For Self-Hosted

1. **Enable Compression**:
   ```nginx
   gzip on;
   gzip_types text/css application/javascript;
   ```

2. **Set Cache Headers**:
   ```nginx
   location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **Use HTTP/2**:
   - Enable HTTP/2 in nginx/Apache
   - Improves parallel loading

## Continuous Deployment

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs
```

This automatically deploys on every push to main.

## Monitoring

### GitHub Pages

- Check deployment status in **Actions** tab
- View build logs for errors
- Use GitHub's status page for outages

### Analytics (Optional)

Add Google Analytics or Plausible to track usage:

```html
<!-- Add to docs/index.html before </head> -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## Security

### GitHub Pages

- Automatically serves over HTTPS
- No server-side code execution
- Safe from SQL injection, XSS (if coded properly)

### Best Practices

1. **Content Security Policy** (add to HTML):
   ```html
   <meta http-equiv="Content-Security-Policy"
         content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';">
   ```

2. **Subresource Integrity** (for CDN files):
   ```html
   <script src="https://cdn.example.com/lib.js"
           integrity="sha384-..."
           crossorigin="anonymous"></script>
   ```

3. **Regular Updates**:
   - Keep dependencies updated
   - Monitor for security advisories

## Rollback

If deployment breaks:

### GitHub Pages

1. Go to **Settings → Pages**
2. Change branch or folder
3. Or revert the commit:
   ```bash
   git revert HEAD
   git push
   ```

### Netlify/Vercel

- Use web UI to roll back to previous deployment
- Every deploy is immutable and saved

## Support

For issues:
- GitHub Pages: [pages.github.com](https://pages.github.com)
- Netlify: [docs.netlify.com](https://docs.netlify.com)
- Vercel: [vercel.com/docs](https://vercel.com/docs)

---

**Current Status**: Web version ready to deploy to GitHub Pages!

After enabling GitHub Pages, your Slitherin game will be live at:
**https://vonalphabiszulu.github.io/slitherin/**
