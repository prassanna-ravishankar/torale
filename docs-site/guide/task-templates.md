# Task Templates

Pre-configured templates for common monitoring scenarios. Get started quickly with tested query and condition patterns.

## Using Templates

### Web Dashboard

1. Click "New Task"
2. Select "Use Template"
3. Browse categories or search
4. Choose template
5. Customize placeholders (product name, price, etc.)
6. Set schedule
7. Create task

### Template Categories

- **Product Releases** - Monitor launch announcements
- **Price Tracking** - Track price changes and deals
- **Stock Availability** - Check inventory status
- **Event Tickets** - Monitor ticket sales
- **News & Announcements** - Stay updated on developments
- **Service Availability** - Track appointments and registrations

## Product Release Templates

### Tech Product Release
Monitor when companies announce release dates for new products.

**Template:**
```
Name: {product} Release Date Monitor
Query: When is {product} being released?
Condition: An official release date or timeframe has been announced
Schedule: Daily at 9 AM
Notify: once
```

**Examples:**
- iPhone 17
- GPT-5
- PlayStation 6
- Tesla Model 2
- Apple Vision Pro 2

### Software Release
Track software and app release dates.

**Template:**
```
Name: {software} Launch Monitor
Query: When is {software} version {version} being released?
Condition: Release date or availability has been officially announced
Schedule: Daily at 9 AM
Notify: once
```

**Examples:**
- iOS 18
- Windows 12
- macOS 15
- Android 15

### Gaming Release
Monitor video game launch dates.

**Template:**
```
Name: {game} Release Date Tracker
Query: When is {game} being released?
Condition: Official release date has been announced by {developer}
Schedule: Daily at 9 AM
Notify: once
```

**Examples:**
- GTA 6
- Elder Scrolls 6
- Minecraft 2
- Half-Life 3

## Price Tracking Templates

### Price Drop Alert
Get notified when product price drops below threshold.

**Template:**
```
Name: {product} Price Alert - {store}
Query: What is the current price of {product} at {store}?
Condition: The price is {target_price} or lower
Schedule: Every 4 hours
Notify: always
```

**Examples:**
- MacBook Pro M3 at Best Buy (target: $1799)
- PS5 at Amazon (target: $449)
- AirPods Pro at Costco (target: $199)

### Deal Tracker
Monitor sales and special offers.

**Template:**
```
Name: {product} Deal Tracker
Query: What are the current deals on {product} at {store}?
Condition: There is a discount of {percent}% or more
Schedule: Every 6 hours
Notify: track_state
```

**Examples:**
- OLED TVs at Best Buy (20% off)
- Nike shoes at Nike.com (30% off)
- Dyson vacuums at Amazon (25% off)

### Travel Price Monitor
Track flight and hotel prices.

**Template:**
```
Name: {route} Flight Price Tracker
Query: What is the price for round-trip flights from {origin} to {destination} in {month}?
Condition: Flights are available for under {max_price}
Schedule: Daily at 8 AM
Notify: always
```

**Examples:**
- SFO to Tokyo in March (under $800)
- LAX to London in June (under $600)
- JFK to Paris in September (under $500)

## Stock Availability Templates

### Console Availability
Monitor gaming console stock.

**Template:**
```
Name: {console} Stock Alert - {store}
Query: Is {console} in stock at {store}?
Condition: {console} is currently available for purchase
Schedule: Every 2 hours
Notify: once
```

**Examples:**
- PS5 at Target
- Xbox Series X at Best Buy
- Nintendo Switch OLED at GameStop

### Limited Edition Items
Track hard-to-find limited releases.

**Template:**
```
Name: {product} Availability Checker
Query: Is {product} available for purchase?
Condition: The item is in stock at any major retailer
Schedule: Every hour
Notify: once
```

**Examples:**
- Analogue Pocket
- Steam Deck Limited Edition
- LEGO UCS Millennium Falcon

### Sneaker Drops
Monitor sneaker releases and restocks.

**Template:**
```
Name: {sneaker} Stock Tracker
Query: Are {sneaker} available on {website}?
Condition: The sneakers are in stock in size {size}
Schedule: Every 15 minutes
Notify: once
```

**Examples:**
- Air Jordan 4 Retro on Nike.com (size 10)
- Yeezy 350 V2 on Adidas.com (size 11)
- Dunk Low on SNKRS (size 9)

## Event Ticket Templates

### Concert Tickets
Monitor when concert tickets go on sale.

**Template:**
```
Name: {artist} Tickets - {city}
Query: Are {artist} concert tickets on sale for {city}?
Condition: Tickets are available for purchase on Ticketmaster or official site
Schedule: Every hour
Notify: once
```

**Examples:**
- Taylor Swift - Los Angeles
- Beyoncé - New York
- Coldplay - Chicago

### Sports Tickets
Track sporting event ticket availability.

**Template:**
```
Name: {event} Ticket Tracker
Query: Are {event} tickets available?
Condition: Tickets are on sale and available for purchase
Schedule: Every 2 hours
Notify: once
```

**Examples:**
- Super Bowl LVIII
- World Series Game 7
- NBA Finals

### Festival Passes
Monitor festival ticket sales.

**Template:**
```
Name: {festival} Pass Alert
Query: Are {festival} passes on sale for {year}?
Condition: Passes or tickets are available for purchase
Schedule: Every hour
Notify: once
```

**Examples:**
- Coachella 2025
- Burning Man 2025
- Lollapalooza 2025

## Service Availability Templates

### Appointment Availability
Monitor government service appointments.

**Template:**
```
Name: {service} Appointment Tracker - {location}
Query: Are {service} appointments available at {location}?
Condition: Appointment slots are open within the next {timeframe}
Schedule: Every 4 hours
Notify: once
```

**Examples:**
- Passport renewal at SF Passport Agency (2 weeks)
- DMV appointments in San Francisco (1 week)
- TSA PreCheck enrollment (1 month)

### Registration Openings
Track when registrations open for programs.

**Template:**
```
Name: {program} Registration Monitor
Query: Are {program} registrations open for {season/period}?
Condition: Registration is now available
Schedule: Daily at 8 AM
Notify: once
```

**Examples:**
- Swimming pool memberships for summer
- Youth soccer league for fall
- Community college classes for spring

### Restaurant Reservations
Monitor hard-to-get reservations (future feature).

**Template:**
```
Name: {restaurant} Reservation Finder
Query: Are reservations available at {restaurant} for {date}?
Condition: At least one reservation slot is open
Schedule: Every 2 hours
Notify: once
```

## News & Announcement Templates

### Company Announcements
Track corporate announcements.

**Template:**
```
Name: {company} Announcement Tracker
Query: Has {company} announced {topic}?
Condition: {company} has officially announced or confirmed {specific_detail}
Schedule: Daily at 9 AM
Notify: once
```

**Examples:**
- Apple announced next event date
- OpenAI announced GPT-5
- Tesla announced Cybertruck pricing

### Policy Updates
Monitor regulatory and policy changes.

**Template:**
```
Name: {topic} Policy Monitor
Query: What is the latest on {topic} {policy/regulation}?
Condition: New developments or official updates have been announced
Schedule: Daily at 9 AM
Notify: track_state
```

**Examples:**
- AI regulation in California
- Crypto legislation in US
- Privacy laws in EU

### Research Publications
Track when research papers are published.

**Template:**
```
Name: {topic} Research Tracker
Query: Has {organization} published {research_topic} paper?
Condition: The paper or technical report is publicly available
Schedule: Every Monday at 9 AM
Notify: once
```

**Examples:**
- DeepMind published Gemini 2.0 paper
- OpenAI published GPT-5 technical report
- Anthropic published Claude 4 paper

## Creating Custom Templates

While templates provide a starting point, you can customize any field:

### Customizing Queries

**Make more specific:**
```
Template: "When is {product} being released?"
Custom: "When is the iPhone 16 Pro Max 1TB being released in the US?"
```

**Add location:**
```
Template: "Is {product} in stock?"
Custom: "Is {product} in stock at Target stores in San Francisco?"
```

### Customizing Conditions

**Add thresholds:**
```
Template: "The price is lower"
Custom: "The price is $1799 or lower and not refurbished"
```

**Add specificity:**
```
Template: "Release date announced"
Custom: "Official release date announced by Apple, not rumors"
```

### Adjusting Schedules

Based on urgency:

**High urgency:** Every 15-60 minutes
```
*/15 * * * *     # Limited drops, tickets
```

**Medium urgency:** Every 2-4 hours
```
0 */2 * * *      # Stock monitoring, appointments
```

**Low urgency:** Daily or weekly
```
0 9 * * *        # News, announcements
0 9 * * 1        # Weekly job postings
```

## Template Best Practices

### Start with Template, Then Refine

1. Choose closest template
2. Create task from template
3. Run immediately to test
4. Adjust query/condition if needed
5. Update schedule based on urgency

### Combine Templates

Create multiple related tasks:

**Example: Complete Product Launch Monitoring**
```
Task 1: Release date announcement (from Product Release template)
Task 2: Pre-order availability (from Stock Availability template)
Task 3: Launch day pricing (from Price Tracking template)
```

### Template Modification Tips

**Too broad?** Add more details to query and condition
**Too narrow?** Remove specific requirements
**Wrong timing?** Adjust schedule frequency
**Wrong notifications?** Change notify_behavior

## Next Steps

- Learn about [Creating Tasks](/guide/creating-tasks) from scratch
- Understand [Scheduling](/guide/scheduling) options
- Configure [Notifications](/guide/notifications)
- Read [Use Cases](/guide/use-cases) for more examples
