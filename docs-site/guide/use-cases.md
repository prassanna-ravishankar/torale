# Use Cases

Torale is designed for monitoring any information that changes over time on the web. Here are common use cases with real-world examples.

## Product Releases

Monitor when companies announce new product releases.

### Tech Products

**iPhone Release Date**
```bash
torale task create \
  --query "When is the next iPhone being released?" \
  --condition "Apple has officially announced a specific release date" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

**GPT-5 Launch**
```bash
torale task create \
  --query "When is GPT-5 being released by OpenAI?" \
  --condition "OpenAI has announced an official release date or timeframe" \
  --schedule "0 */6 * * *" \
  --notify-behavior once
```

**Gaming Consoles**
```bash
torale task create \
  --query "When is the PS6 release date?" \
  --condition "Sony has officially announced PS6 and its release date" \
  --schedule "0 9 * * 1" \
  --notify-behavior once
```

## Price Tracking

Monitor price changes for products you want to buy.

### Electronics

**MacBook Price Drop**
```bash
torale task create \
  --query "What is the current price of MacBook Pro M3 14-inch at Best Buy?" \
  --condition "The price is $1799 or lower" \
  --schedule "0 */4 * * *" \
  --notify-behavior always
```

**Black Friday Deals**
```bash
torale task create \
  --query "What are the current Black Friday deals on Sony TVs at Amazon?" \
  --condition "A 65-inch OLED is priced below $1200" \
  --schedule "0 */2 * * *" \
  --notify-behavior always
```

### Travel

**Flight Price Monitoring**
```bash
torale task create \
  --query "What is the current price for round-trip flights from SFO to Tokyo in March?" \
  --condition "Flights are available for under $800" \
  --schedule "0 8 * * *" \
  --notify-behavior always
```

**Hotel Deals**
```bash
torale task create \
  --query "What are hotel rates at Marriott Waikiki for summer 2024?" \
  --condition "Rates have dropped below $200 per night" \
  --schedule "0 9 * * *" \
  --notify-behavior track_state
```

## Stock & Availability

Track when out-of-stock items become available.

### Product Availability

**Gaming Consoles**
```bash
torale task create \
  --query "Is PlayStation 5 in stock at Target?" \
  --condition "PS5 is currently available for purchase online" \
  --schedule "0 */2 * * *" \
  --notify-behavior once
```

**Limited Edition Items**
```bash
torale task create \
  --query "Is the Nintendo Switch OLED Zelda Edition in stock?" \
  --condition "The item is available for purchase at any major retailer" \
  --schedule "0 */1 * * *" \
  --notify-behavior once
```

**Sneaker Drops**
```bash
torale task create \
  --query "Are the Air Jordan 4 Retro available on Nike.com?" \
  --condition "The sneakers are in stock in size 10" \
  --schedule "0 */15 * * * *" \
  --notify-behavior once
```

## Event & Ticket Monitoring

Get notified when tickets go on sale or events are announced.

### Concerts & Shows

**Concert Tickets**
```bash
torale task create \
  --query "Are Taylor Swift Eras Tour tickets on sale for Los Angeles?" \
  --condition "Tickets are available for purchase on Ticketmaster" \
  --schedule "0 */1 * * *" \
  --notify-behavior once
```

**Broadway Shows**
```bash
torale task create \
  --query "Are Hamilton tickets available for September in NYC?" \
  --condition "Tickets are on sale for performances in September" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

### Sports Events

**Super Bowl Tickets**
```bash
torale task create \
  --query "What is the current price for Super Bowl LVIII tickets?" \
  --condition "Tickets are available for under $5000" \
  --schedule "0 */6 * * *" \
  --notify-behavior track_state
```

## Service Availability

Monitor when services, registrations, or bookings open.

### Recreation & Fitness

**Pool Memberships**
```bash
torale task create \
  --query "Are swimming pool memberships open for summer at SF Recreation Center?" \
  --condition "Summer memberships are now available for registration" \
  --schedule "0 8 * * *" \
  --notify-behavior once
```

**Gym Class Bookings**
```bash
torale task create \
  --query "Is Barry's Bootcamp 6am class available on Saturday?" \
  --condition "Spots are open for booking" \
  --schedule "0 */2 * * *" \
  --notify-behavior once
```

### Government Services

**Passport Appointments**
```bash
torale task create \
  --query "Are passport renewal appointments available at SF Passport Agency?" \
  --condition "Appointment slots are open within the next 2 weeks" \
  --schedule "0 */4 * * *" \
  --notify-behavior once
```

**DMV Appointments**
```bash
torale task create \
  --query "Are DMV appointments available in San Francisco for driver's license renewal?" \
  --condition "Appointments are available within the next week" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

## News & Announcements

Stay updated on specific topics or developments.

### Tech Announcements

**Company Announcements**
```bash
torale task create \
  --query "Has Apple announced their next event date?" \
  --condition "Apple has officially announced a product event with a specific date" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

**Feature Launches**
```bash
torale task create \
  --query "Has OpenAI released GPT-4 Turbo with vision API?" \
  --condition "The API is generally available for all users" \
  --schedule "0 */6 * * *" \
  --notify-behavior once
```

### Regulatory & Legal

**Policy Changes**
```bash
torale task create \
  --query "Has the FTC announced new AI regulation guidelines?" \
  --condition "Official guidelines have been published" \
  --schedule "0 9 * * *" \
  --notify-behavior track_state
```

### Industry News

**Funding Announcements**
```bash
torale task create \
  --query "Has Anthropic announced a new funding round?" \
  --condition "A funding round with amount has been officially announced" \
  --schedule "0 9 * * 1" \
  --notify-behavior once
```

## Real Estate

Monitor property listings and price changes.

### Housing

**New Listings**
```bash
torale task create \
  --query "Are there new 2-bedroom apartments listed in Hayes Valley SF under $3500?" \
  --condition "At least one new listing matches criteria" \
  --schedule "0 9,17 * * *" \
  --notify-behavior always
```

**Price Reductions**
```bash
torale task create \
  --query "Have any 3-bedroom homes in Palo Alto reduced prices?" \
  --condition "Listings show price reductions in the last 7 days" \
  --schedule "0 9 * * *" \
  --notify-behavior track_state
```

## Job Postings

Track job openings at specific companies.

**Company Job Openings**
```bash
torale task create \
  --query "Are there new Senior Software Engineer positions at Anthropic?" \
  --condition "At least one position is listed on Anthropic's careers page" \
  --schedule "0 9 * * 1,3,5" \
  --notify-behavior always
```

**Remote Positions**
```bash
torale task create \
  --query "Are there remote machine learning engineer positions at OpenAI?" \
  --condition "Remote ML engineering roles are listed" \
  --schedule "0 9 * * *" \
  --notify-behavior always
```

## Academic & Research

Monitor research publications, conference dates, and application deadlines.

### Conferences

**Conference Dates**
```bash
torale task create \
  --query "When is NeurIPS 2025 taking place?" \
  --condition "Official dates and location have been announced" \
  --schedule "0 9 * * 1" \
  --notify-behavior once
```

**Paper Submissions**
```bash
torale task create \
  --query "When is the submission deadline for ICML 2025?" \
  --condition "The final submission deadline has been announced" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

### Publications

**Research Papers**
```bash
torale task create \
  --query "Has DeepMind published their Gemini 2.0 technical report?" \
  --condition "The technical report or paper is publicly available" \
  --schedule "0 9 * * *" \
  --notify-behavior once
```

## Weather & Natural Events

Track weather patterns and natural phenomena.

**Surf Conditions**
```bash
torale task create \
  --query "What are the surf conditions at Ocean Beach SF this week?" \
  --condition "Wave height is 6 feet or higher" \
  --schedule "0 6 * * *" \
  --notify-behavior track_state
```

**Aurora Forecast**
```bash
torale task create \
  --query "Is the Northern Lights visible in Iceland this weekend?" \
  --condition "KP index is 5 or higher indicating strong aurora activity" \
  --schedule "0 */3 * * *" \
  --notify-behavior track_state
```

## Best Practices

### Choosing Notification Behavior

- **`once`** - One-time events (releases, announcements, openings)
- **`always`** - Recurring events (prices, availability checks)
- **`track_state`** - Evolving information (news, status updates)

### Schedule Recommendations

- **Time-sensitive** (tickets, drops) - Every 1-2 hours or more frequent
- **Daily updates** (news, announcements) - Once or twice per day
- **Price monitoring** - Every 4-6 hours
- **Weekly checks** (job postings) - 2-3 times per week

### Writing Effective Queries

- Be specific about what you're looking for
- Include relevant details (location, model, size, etc.)
- Focus on a single topic per task
- Use natural language

### Crafting Good Conditions

- State exact criteria that can be objectively evaluated
- Avoid vague terms like "good deal" or "interesting"
- Include specific thresholds for numbers (prices, dates)
- Be clear about what constitutes a match

## Next Steps

- Learn how to [create tasks](/guide/creating-tasks)
- Use [task templates](/guide/task-templates) for quick setup
- Configure [notifications](/guide/notifications)
- Master [scheduling](/guide/scheduling)
