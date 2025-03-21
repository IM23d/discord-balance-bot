import discord
from discord.ext import commands
import json
import os
import random
import datetime

class EconomyCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        
    @commands.command()
    async def balance(self, ctx):
        await self.open_account(ctx.author)
        user = ctx.author
        users = await self.get_bank_data()

        wallet_amt = users[str(ctx.author.id)]["wallet"]
        bank_amt = users[str(ctx.author.id)]["bank"]

        em = discord.Embed(title=f"{ctx.author.name}'s balance", color=discord.Color.red())
        em.add_field(name="Wallet balance", value=wallet_amt)
        em.add_field(name="Bank balance", value=bank_amt)
        await ctx.send(embed=em)

    @commands.command()
    async def bal(self, ctx):
        await self.balance(ctx)
    
    @commands.command()
    @commands.cooldown(1, 86400, commands.BucketType.user)  # 1 day cooldown
    async def beg(self, ctx):
        import random
        
        await self.open_account(ctx.author)
        users = await self.get_bank_data()
        user = ctx.author
        
        earnings = random.randrange(101)  # amount the user gets for -beg = max 101
        
        embed = discord.Embed(
            title="Begging Results",
            description=f"Diddy gave you **{earnings} coins**!",
            color=discord.Color.green()
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        
        new_balance = users[str(ctx.author.id)]["wallet"] + earnings
        embed.add_field(
            name="New Wallet Balance", 
            value=f"{new_balance} coins",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
        
        users[str(ctx.author.id)]["wallet"] += earnings
        
        with open('data/bank.json', 'w') as f:
            json.dump(users, f)

    @beg.error  # error handling for -beg
    async def beg_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            hours, remainder = divmod(error.retry_after, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="Cooldown Active",
                description="You've already begged recently!",
                color=discord.Color.red()
            )
            
            embed.add_field(
                name="Time Remaining",
                value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
                inline=False
            )
                        
            embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
            embed.timestamp = datetime.datetime.utcnow()
            
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Error Occurred",
                description=f"An unexpected error happened: {str(error)}",
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="Please report this to the admins")
            await ctx.send(embed=embed)
    
    async def open_account(self, user):
        users = await self.get_bank_data()

        if str(user.id) in users:
            return False
        else:
            users[str(user.id)] = {}
            users[str(user.id)]["wallet"] = 0  # starting balance
            users[str(user.id)]["bank"] = 0

        with open('data/bank.json', 'w') as f:  # opens account for new user
            json.dump(users, f)
        return True
    
    async def get_bank_data(self):
        if not os.path.exists('data'):
            os.makedirs('data')
        
        if not os.path.exists('data/bank.json'):
            with open('data/bank.json', 'w') as f:
                json.dump({}, f)

        with open('data/bank.json', 'r') as f:
            content = f.read().strip()
            if not content:
                users = {}
            else:
                try:
                    users = json.loads(content)
                except json.JSONDecodeError:
                    users = {}
            
        if not content:
            with open('data/bank.json', 'w') as f:
                json.dump(users, f)
                
        return users