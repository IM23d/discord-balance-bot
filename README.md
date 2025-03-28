# Discord Balance Bot

A simple Discord balance bot to track virtual currency in your server.

## Commands

Below is a list of available commands, grouped by their respective categories.


### AdminCog

- **`-addbalance <user> <amount>`**  
  Adds a specified amount to a user's balance.
  
- **`-ban <user>`**  
  Bans a member from the server.
  
- **`-kick <user>`**  
  Kicks a member from the server.
  
- **`-removebalance <user> <amount>`**  
  Removes a specified amount from a user's balance.
### EconomyCog

- **`-bal`**  
  Alias for `-balance`. Check your virtual currency balance.
  
- **`-balance`**  
  Check your virtual currency balance.
  
- **`-balancetop`**  
  Displays the server's balance leaderboard.
  
- **`-beg`**  
  Gives the user a random amount of money (1-100) and shows the new wallet balance. Has a 24-hour cooldown.
  
- **`-dep`**  
  Alias for `-deposit`. Deposit money into your account.
  
- **`-deposit <amount>`**  
  Deposit a specified amount (number, percentage like "50%", or "all") into your bank account from your wallet.
  
- **`-withdraw <amount>`**  
  Withdraw a specified amount (number, percentage like "50%", or "all") from your bank account to your wallet.
  
- **`-wit`**  
  Alias for `-withdraw`. Withdraw money from your account.

### GamblingCog

- **`-gamble <amount>`**  
  Gamble a specified amount of virtual currency. Heads or Tails.

### JobMarketCog

- **`-jobs [page]`**  
  Display available jobs in the job market with pagination (default page is 1). Shows job details and unlock status.
  
- **`-buyjob <job>`**  
  Purchase a job to unlock it. Costs coins based on the job's unlock price. Maximum of 3 jobs allowed at a time.
  
- **`-work`**  
  Work at all your unlocked jobs to earn money (base pay + possible bonus). Has a 24-hour cooldown.
  
- **`-removejob <job>`**  
  Remove a job from your current jobs list to free up a slot.
  
- **`-myjobs`**  
  Display your currently owned jobs with their details.


### LastFMcog

- **`-lastfm`**  
  Displays information about your Last.fm account.

- **`-login`**  
  Logs into your Last.fm account.

- **`-np`**  
  Displays the currently playing song on Last.fm.


### LevelsCog

- **`-level [user]`**  
  Shows your level or another member's level.

- **`-levels`**  
  Displays the server's level leaderboard.

  
### OtherCog

- **`-code`**  
  Outputs a secret code.
  
- **`-david`**  
  Shares a random meme about David and his Raspberry Pi (image or GIF).
  
- **`-dsl`**  
  Sends a link to [https://habenwirmorgenopl.info](https://habenwirmorgenopl.info) (might be down) in the chat.
  
- **`-geschichte`**  
  Tells a short story about Milan and David.
  
- **`-hwmo`**  
  Sends a link to [https://habenwirmorgenopl.info](https://habenwirmorgenopl.info) (might be down) in the chat.
  
- **`-opl`**  
  Sends a link to [https://habenwirmorgenopl.info](https://habenwirmorgenopl.info) (might be down) in the chat.
  
- **`-ppl`**  
  Sends a link to [https://habenwirmorgenopl.info](https://habenwirmorgenopl.info) (might be down) in the chat.
  
- **`-info`**  
  Displays information about the bot, including GitHub repository, developers, contributors, and version.
  
- **`-hi`**  
  Responds with "Hi I'm coffee!".
  
- **`-github`**  
  Sends a link to GitHub's pull request documentation.

- **`-lyric`**  
 Outputs a random lyric from the song "Call Me Maybe".

### No Category

- **`-help`**  
  Shows this message with a list of available commands and their descriptions.
  
- **`-help <command>`**  
  Shows detailed information about a specific command.

- **`-help <category>`**  
  Shows detailed information about a specific category.
