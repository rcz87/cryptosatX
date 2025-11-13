# CryptoSatX Dashboard

Modern, interactive dashboard for monitoring AI-powered crypto trading signals in real-time.

## Features

### 📊 Real-Time Analytics
- Live signal monitoring with auto-refresh (30s)
- AI verdict performance tracking
- Signal distribution visualizations
- Performance timeline with cumulative P&L

### 🎨 Modern UI/UX
- Tailwind CSS for beautiful, responsive design
- Dark mode support with localStorage persistence
- Card-based layout inspired by LunarCrush and Coinglass
- Smooth animations and transitions
- Mobile-friendly responsive design

### 📈 Interactive Charts
- **Verdict Performance Chart**: Win rates by AI verdict type (CONFIRM/DOWNSIZE/SKIP/WAIT)
- **Signal Distribution**: Pie chart showing LONG/SHORT/NEUTRAL distribution
- **Performance Timeline**: Line chart tracking cumulative P&L over time

### ⚡ Quick Features
- Quick signal generator with popular asset buttons
- Real-time signal results with AI verdict analysis
- Filterable signal history
- Live system status indicator

## Tech Stack

- **Frontend**: Pure HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Tailwind CSS 3.x
- **Charts**: Chart.js 4.4
- **Icons**: Font Awesome 6.4
- **Fonts**: Google Fonts (Inter)

## File Structure

```
static/
├── dashboard/
│   ├── index.html       # Main dashboard HTML
│   └── README.md        # This file
└── js/
    └── dashboard.js     # Dashboard logic and API integration
```

## API Endpoints Used

The dashboard integrates with the following CryptoSatX API endpoints:

- `GET /signals/{symbol}` - Generate trading signal
- `GET /analytics/verdict-performance` - Get AI verdict performance metrics
- `GET /analytics/outcomes-history` - Get signal outcomes history
- `GET /analytics/tracking-stats` - Get overall tracking statistics

## Access

- **Homepage**: `https://guardiansofthetoken.org/`
- **Dashboard**: `https://guardiansofthetoken.org/dashboard`
- **API Docs**: `https://guardiansofthetoken.org/docs`

## Features Breakdown

### Stats Cards
1. **Total Signals**: Count of all generated signals
2. **AI Win Rate**: 24h win rate percentage
3. **Active Signals**: Signals currently being tracked
4. **Avg P&L**: Average profit/loss in 24h period

### Latest Signals Panel
- Displays last 10 signals with full details
- Color-coded by signal type (LONG=green, SHORT=red)
- Shows AI verdict, P&L, and outcome status
- Hover effects for better UX

### Quick Signal Generator
- Text input for any cryptocurrency symbol
- One-click generation from popular assets
- Beautiful result display with full signal details
- Shows AI verdict summary and top reasons

## Dark Mode

The dashboard supports dark mode with automatic theme persistence:
- Toggle via moon/sun icon in navigation
- Theme saved to localStorage
- Automatically applied on page load
- Smooth color transitions

## Performance

- Auto-refresh every 30 seconds
- Manual refresh button available
- Optimized API calls with error handling
- Efficient chart updates without full re-render
- Lazy loading for better initial load time

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Development

To modify the dashboard:

1. Edit `static/dashboard/index.html` for HTML structure
2. Edit `static/js/dashboard.js` for functionality
3. Tailwind CSS classes are loaded from CDN
4. Charts are rendered with Chart.js
5. No build process required - pure static files

## Customization

### Change Refresh Interval
Edit `dashboard.js`:
```javascript
const REFRESH_INTERVAL = 30000; // Change to desired ms
```

### Modify Colors
Dashboard uses Tailwind CSS color system. Modify in the HTML:
```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#3b82f6', // Change primary color
                // ... other colors
            }
        }
    }
}
```

### Add More Charts
Use Chart.js in `dashboard.js`:
```javascript
const newChart = new Chart(ctx, {
    type: 'bar', // or 'line', 'doughnut', etc.
    data: { ... },
    options: { ... }
});
```

## Future Enhancements

- [ ] WebSocket integration for real-time updates
- [ ] User authentication and personalized dashboards
- [ ] Alert notifications (browser push)
- [ ] Portfolio tracking
- [ ] Backtesting visualization
- [ ] Export reports to PDF
- [ ] Advanced filtering and search
- [ ] Multi-timeframe analysis
- [ ] Social sharing features
- [ ] Custom dashboard widgets

## License

Proprietary - Part of CryptoSatX Trading System

---

**Built with ❤️ for crypto traders**
