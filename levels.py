import discord
from discord.ext import commands
import json
import os
import math
import datetime
import random

class LevelsCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        # XP settings
        self.base_xp = 15  # Base XP per message
        self.xp_per_level = 7500  # XP needed for each level (500 messages = one level)
        self.message_count = {}  # Track messages per minute
        self.window_start = {}  # Track when the 60-second window started
        # Voice tracking
        self.voice_time = {}  # Track current voice sessions
        self.voice_start = {}  # Track when users joined VC
        
    @commands.Cog.listener()
    async def on_message(self, message):
        # Don't process bot messages or commands
        if message.author.bot or message.content.startswith(self.client.command_prefix):
            return
            
        # Handle XP gain
        await self.add_xp(message.author, message.channel)
        
    async def update_voice_time(self, member):
        """Update voice time for users currently in voice chat"""
        if not member.voice or member.voice.afk:
            return
            
        user_id = str(member.id)
        current_time = datetime.datetime.now().timestamp()
        
        # If user is in voice but not being tracked, start tracking them
        if user_id not in self.voice_start and member.voice and not member.voice.afk:
            self.voice_start[user_id] = current_time
            self.voice_time[user_id] = 0
            # Create user entry in voice data
            await self.check_voice_user(member)
            return
            
        # If user is being tracked, update their time
        if user_id in self.voice_start:
            time_spent = current_time - self.voice_start[user_id]
            
            # Update voice data
            voice_users = await self.get_voice_data()
            await self.check_voice_user(member)  # Ensure user exists in database
            
            # Add time spent to total
            voice_users[user_id]["voice_time"] = voice_users[user_id].get("voice_time", 0) + time_spent
            
            # Save voice data
            with open('data/voice_levels.json', 'w') as f:
                json.dump(voice_users, f)
                
            # Update tracking with new start time
            self.voice_start[user_id] = current_time
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = str(member.id)
        current_time = datetime.datetime.now().timestamp()
        
        # Ignore AFK channel
        if after.channel and after.channel.afk:
            return
            
        # User joined a voice channel
        if not before.channel and after.channel:
            self.voice_start[user_id] = current_time
            self.voice_time[user_id] = 0
            
        # User left a voice channel
        elif before.channel and not after.channel:
            if user_id in self.voice_start:
                # Calculate time spent
                time_spent = current_time - self.voice_start[user_id]
                
                # Update voice data
                voice_users = await self.get_voice_data()
                await self.check_voice_user(member)
                
                # Add time spent to total
                voice_users[user_id]["voice_time"] = voice_users[user_id].get("voice_time", 0) + time_spent
                
                # Save voice data
                with open('data/voice_levels.json', 'w') as f:
                    json.dump(voice_users, f)
                    
                # Clean up tracking
                del self.voice_start[user_id]
                del self.voice_time[user_id]
                
        # User switched channels
        elif before.channel and after.channel and before.channel != after.channel:
            # If moving to AFK, count it as leaving
            if after.channel.afk:
                if user_id in self.voice_start:
                    time_spent = current_time - self.voice_start[user_id]
                    voice_users = await self.get_voice_data()
                    await self.check_voice_user(member)
                    
                    voice_users[user_id]["voice_time"] = voice_users[user_id].get("voice_time", 0) + time_spent
                    
                    with open('data/voice_levels.json', 'w') as f:
                        json.dump(voice_users, f)
                    del self.voice_start[user_id]
                    del self.voice_time[user_id]
            # If moving from AFK to normal channel, count as joining
            elif before.channel.afk and not after.channel.afk:
                self.voice_start[user_id] = current_time
                self.voice_time[user_id] = 0
        
    async def add_xp(self, user, channel):
        # Anti-spam mechanism (max 60 messages per minute)
        user_id = str(user.id)
        current_time = datetime.datetime.now().timestamp()
        
        # Initialize tracking for new users
        if user_id not in self.message_count:
            self.message_count[user_id] = 0
            self.window_start[user_id] = current_time
        
        # Check if 60 seconds have passed, reset if true
        if current_time - self.window_start[user_id] > 60:
            self.message_count[user_id] = 0
            self.window_start[user_id] = current_time
        
        # Increment message count and check if under limit
        self.message_count[user_id] += 1
        if self.message_count[user_id] > 60:
            return  # Over rate limit, don't add XP
                
        # Add XP with some randomness
        xp_gained = self.base_xp + random.randint(-5, 5)
        if xp_gained < 5:
            xp_gained = 5  # Minimum XP gain
            
        # Get current user data
        users = await self.get_levels_data()
        await self.check_user(user)
        
        # Get current level
        current_level = users[user_id]["level"]
        current_xp = users[user_id]["xp"]
        new_xp = current_xp + xp_gained
        
        # Calculate if user leveled up
        level_up = False
        new_level = math.floor(new_xp / self.xp_per_level)
        
        if new_level > current_level:
            level_up = True
            users[user_id]["level"] = new_level
            
        # Update user data
        users[user_id]["xp"] = new_xp
        users[user_id]["total_messages"] += 1
        users[user_id]["last_message"] = current_time
        
        # Save data
        with open('data/levels.json', 'w') as f:
            json.dump(users, f)
            
        # Send level up message if user leveled up
        if level_up and channel:
            embed = discord.Embed(
                title="LEVEL UP! 🎉",
                description=f"Congratulations {user.mention}! You've reached **Level {new_level}**!",
                color=discord.Color.gold()
            )
            embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            await channel.send(embed=embed)
    
    @commands.command(aliases=["xp", "lvl"])
    async def level(self, ctx, member: discord.Member = None):
        """Check your level or another member's level"""
        if member is None:
            member = ctx.author
            
        # Update voice time if user is in voice
        await self.update_voice_time(member)
            
        await self.check_user(member)
        await self.check_voice_user(member)
        users = await self.get_levels_data()
        voice_users = await self.get_voice_data()
        user_id = str(member.id)
        
        # Get message data
        xp = users[user_id]["xp"]
        level = users[user_id]["level"]
        total_messages = users[user_id]["total_messages"]
        
        # Get voice data
        voice_time = voice_users[user_id]["voice_time"]
        
        # Calculate message progress to next level
        xp_for_current_level = level * self.xp_per_level
        xp_for_next_level = (level + 1) * self.xp_per_level
        current_level_xp = xp - xp_for_current_level
        needed_for_next_level = xp_for_next_level - xp_for_current_level
        percentage = min(100, max(0, int((current_level_xp / needed_for_next_level) * 100)))
        
        # Create progress bar
        progress_bar = self.create_progress_bar(percentage)
        
        # Format voice time
        hours = int(voice_time / 3600)
        minutes = int((voice_time % 3600) / 60)
        voice_time_str = f"{hours}h {minutes}m"
        
        # Create embed
        embed = discord.Embed(
            title=f"{member.name}'s Stats",
            color=discord.Color.blue()
        )
        
        # Message stats
        embed.add_field(name="Level", value=f"**{level}**", inline=True)
        embed.add_field(name="Total XP", value=f"**{xp}**", inline=True)
        embed.add_field(name="Messages", value=f"**{total_messages}**", inline=True)
        embed.add_field(name=f"Progress to Level {level+1}", value=f"{progress_bar} **{percentage}%**\n{current_level_xp}/{needed_for_next_level} XP", inline=False)
        
        # Voice stats
        embed.add_field(name="Time in Voice", value=f"**{voice_time_str}**", inline=True)
        
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
    def create_progress_bar(self, percentage, length=10):
        """Creates a text-based progress bar"""
        filled_bars = math.floor(percentage / (100 / length))
        empty_bars = length - filled_bars
        return "🟦" * filled_bars + "⬜" * empty_bars
        
    @commands.command(aliases=["lvltop"])
    async def levels(self, ctx, page: int = 1):
        """Show the server's message level leaderboard"""
        # Get all user data from the database file directly
        users = await self.get_levels_data()
        
        # Create list from all users in the database
        user_list = []
        
        # First, add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object, fetch from Discord if needed
                member = ctx.guild.get_member(int(user_id))
                
                # Include all users in the database
                if 'xp' in user_data:
                    # Get user data
                    user_entry = {
                        "id": user_id,
                        "xp": user_data["xp"],
                        "level": user_data["level"],
                        "total_messages": user_data["total_messages"],
                        "member": member
                    }
                    user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Sort by level first, then by XP (both descending)
        user_list.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"🏆 Message Level Leaderboard",
            description=f"Top members ranked by message level and XP.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have earned XP yet! Send some messages to start gaining levels."
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"Level: **{user_data['level']}** | XP: **{user_data['xp']}**\nMessages: **{user_data['total_messages']}**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create view with pagination buttons
        view = LevelLeaderboardView(self, ctx, page, total_pages)
        
        # Send embed with view
        view.message = await ctx.send(embed=embed, view=view)

    @commands.command(aliases=["voicetop", "vtop"])
    async def voicelevels(self, ctx, page: int = 1):
        """Show the server's voice time leaderboard"""
        # Update voice time for all users in voice
        for member in ctx.guild.members:
            if member.voice and not member.voice.afk:
                try:
                    # If user is in voice but not being tracked, start tracking them
                    user_id = str(member.id)
                    if user_id not in self.voice_start:
                        current_time = datetime.datetime.now().timestamp()
                        self.voice_start[user_id] = current_time
                        self.voice_time[user_id] = 0
                        # Create user entry in voice data
                        await self.check_voice_user(member)
                    # Update their current time
                    await self.update_voice_time(member)
                except Exception as e:
                    print(f"Error updating voice time for {member.name}: {e}")
                    continue
        
        # Get all user data from the database file directly
        users = await self.get_voice_data()
        
        # Create list from all users in the database
        user_list = []
        
        # First, add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object, fetch from Discord if needed
                member = ctx.guild.get_member(int(user_id))
                
                # Skip if member not found in guild
                if not member:
                    continue
                
                # Format voice time
                voice_time = user_data.get("voice_time", 0)
                
                # If user is currently in voice, add their current session time
                if member and member.voice and not member.voice.afk and user_id in self.voice_start:
                    current_time = datetime.datetime.now().timestamp()
                    current_session = current_time - self.voice_start[user_id]
                    voice_time += current_session
                
                hours = int(voice_time / 3600)
                minutes = int((voice_time % 3600) / 60)
                voice_time_str = f"{hours}h {minutes}m"
                
                # Get user data
                user_entry = {
                    "id": user_id,
                    "voice_time": voice_time,
                    "voice_time_str": voice_time_str,
                    "member": member
                }
                user_list.append(user_entry)
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
                continue
        
        # Sort by voice time (descending)
        user_list.sort(key=lambda x: x["voice_time"], reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        page = max(1, min(page, total_pages))
        
        start_idx = (page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"🎤 Voice Time Leaderboard",
            description=f"Top members ranked by time spent in voice channels.",
            color=discord.Color.purple()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have spent time in voice channels yet!"
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"Time in Voice: **{user_data['voice_time_str']}**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {page}/{total_pages} • Requested by {ctx.author.name}", 
                         icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create view with pagination buttons
        view = LevelLeaderboardView(self, ctx, page, total_pages)
        
        # Send embed with view
        view.message = await ctx.send(embed=embed, view=view)
        
    async def check_user(self, user):
        """Check if user exists in database, create if not"""
        users = await self.get_levels_data()
        user_id = str(user.id)
        
        if user_id not in users:
            users[user_id] = {
                "xp": 0,
                "level": 0,
                "total_messages": 0,
                "last_message": 0
            }
            
            # Save updated data
            with open('data/levels.json', 'w') as f:
                json.dump(users, f)
                
        return True
        
    async def get_levels_data(self):
        """Get level data from JSON file"""
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists('data/levels.json'):
            with open('data/levels.json', 'w') as f:
                json.dump({}, f)

        with open('data/levels.json', 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open('data/levels.json', 'w') as f:
                json.dump(users, f)
                
        return users

    async def get_voice_data(self):
        """Get voice level data from JSON file"""
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists('data/voice_levels.json'):
            with open('data/voice_levels.json', 'w') as f:
                json.dump({}, f)

        with open('data/voice_levels.json', 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open('data/voice_levels.json', 'w') as f:
                json.dump(users, f)
                
        return users

    async def check_voice_user(self, user):
        """Check if user exists in voice database, create if not"""
        users = await self.get_voice_data()
        user_id = str(user.id)
        
        if user_id not in users:
            users[user_id] = {
                "voice_time": 0
            }
            
            # Save updated data
            with open('data/voice_levels.json', 'w') as f:
                json.dump(users, f)
                
        return True

class LevelLeaderboardView(discord.ui.View):
    def __init__(self, cog, ctx, page, total_pages):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.page = page
        self.total_pages = total_pages
        
        # Add previous page button if not on first page
        if page > 1:
            prev_button = discord.ui.Button(
                label="Previous",
                style=discord.ButtonStyle.primary,
                emoji="⬅️",
                custom_id="prev_page",
                row=0
            )
            prev_button.callback = self.prev_callback
            self.add_item(prev_button)
        
        # Add next page button if not on last page
        if page < total_pages:
            next_button = discord.ui.Button(
                label="Next",
                style=discord.ButtonStyle.primary,
                emoji="➡️",
                custom_id="next_page",
                row=0
            )
            next_button.callback = self.next_callback
            self.add_item(next_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("This menu is not for you!", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except:
            pass

    async def update_page(self, new_page: int):
        # Get all user data from database 
        users = await self.cog.get_levels_data()
        
        # Create list from all users in the database
        user_list = []
        
        # Add all existing database entries
        for user_id, user_data in users.items():
            try:
                # Try to get the member object
                member = self.ctx.guild.get_member(int(user_id))
                
                # Include all users in the database
                if 'xp' in user_data:
                    # Get user data
                    voice_time = user_data.get("voice_time", 0)
                    hours = int(voice_time / 3600)
                    minutes = int((voice_time % 3600) / 60)
                    voice_time_str = f"{hours}h {minutes}m"
                    
                    user_entry = {
                        "id": user_id,
                        "xp": user_data["xp"],
                        "level": user_data["level"],
                        "total_messages": user_data["total_messages"],
                        "voice_time": voice_time,
                        "voice_time_str": voice_time_str,
                        "member": member
                    }
                    user_list.append(user_entry)
            except Exception as e:
                # Skip problematic entries
                continue
        
        # Sort by level first, then by XP (both descending)
        user_list.sort(key=lambda x: (x["level"], x["xp"]), reverse=True)
        
        # Paginate results (10 per page)
        total_pages = max(1, math.ceil(len(user_list) / 10))
        
        # Ensure page is within valid range
        new_page = max(1, min(new_page, total_pages))
        
        start_idx = (new_page - 1) * 10
        end_idx = min(start_idx + 10, len(user_list))
        
        # Create embed
        embed = discord.Embed(
            title=f"🏆 Level Leaderboard",
            description=f"Top members ranked by level and XP.",
            color=discord.Color.gold()
        )
        
        # Add leaderboard entries
        if not user_list:
            embed.description = "No users have earned XP yet! Send some messages to start gaining levels."
        else:
            # Get rank emojis for top 3
            rank_emoji = {0: "🥇", 1: "🥈", 2: "🥉"}
            
            for idx, user_data in enumerate(user_list[start_idx:end_idx], start=start_idx + 1):
                member = user_data["member"]
                user_id = user_data["id"]
                position = idx - 1 + start_idx  # Zero-based position
                
                # Get appropriate emoji based on rank
                prefix = rank_emoji.get(position, f"{idx}.")
                
                # Get the name and icon url
                if member:
                    name = member.name
                    icon_url = member.avatar.url if member.avatar else member.default_avatar.url
                else:
                    # Try to fetch user info from Discord
                    try:
                        user = await self.cog.client.fetch_user(int(user_id))
                        name = user.name
                        icon_url = user.avatar.url if user.avatar else user.default_avatar.url
                    except:
                        # If all else fails, use a generic name
                        name = f"User-{user_id[-4:]}"
                        icon_url = None
                
                # Create embed field
                field_name = f"{prefix} {name}"
                field_value = f"Level: **{user_data['level']}** | XP: **{user_data['xp']}**\nMessages: **{user_data['total_messages']}** | Voice: **{user_data['voice_time_str']}**"
                
                embed.add_field(name=field_name, value=field_value, inline=False)
                
                # Show first-place user as thumbnail
                if position == 0 and icon_url:
                    embed.set_thumbnail(url=icon_url)
        
        embed.set_footer(text=f"Page {new_page}/{total_pages} • Requested by {self.ctx.author.name}", 
                         icon_url=self.ctx.author.avatar.url if self.ctx.author.avatar else self.ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        # Create new view with updated page
        new_view = LevelLeaderboardView(self.cog, self.ctx, new_page, total_pages)
        new_view.message = self.message
        
        # Update the message
        await self.message.edit(embed=embed, view=new_view)

    async def prev_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page - 1)

    async def next_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.update_page(self.page + 1)

async def setup(client):
    await client.add_cog(LevelsCog(client)) 