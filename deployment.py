import discord
from discord.ext import commands
import sqlite3
import datetime

bot = discord.Bot(intents=discord.Intents.all())
print("[PYCORD] Bot created successfully.")

pad = bot.create_group("pad", "Public Affairs Department's commands.")
hrd = bot.create_group("hrd", "Human Resources Department's commands.")
qd = bot.create_group("qd", "Qualifications Department's commands.")
ted = bot.create_group("ted", "Training and Education Subdepartment's commands.")
setup = bot.create_group("setup", "Setup commands for SVR+. Used when hiring and/or firing an agent.")
exec = bot.create_group("exec", "Executive commands")

dbfile = "deployment.db"

try:
    dbcon = sqlite3.connect(dbfile)
    print("[DATABASE] SQLite connected successfully.")
    cursor = dbcon.cursor()
    print("[DATABASE] SQLite cursor created successfully.")
except sqlite3.Error as error:
    print(f"[DATABASE] SQLite connection failed. {error} Exiting program.")
    exit()

TOKEN = "changed"
GUILDID = 714808342031237162
guild = None
cguild = None

CODETORANK = {
    "DRT": 1,
    "DDT": 2,
    "FDR": 3,
    "RTD": 4,
    "RDT": 5,
    "AEX": 6,
    "DRH": 7,
    "ADH": 8,
    "DAS": 9,
    "SVR": 10,
    "SGT": 11,
    "AGT": 12,
    "SPN": 13,
    "IRT": 14,
    "PBT": 15,
    "ATR": 16,
    "WMB": 17,
    "RTR": 18
}

RANKTOCODE = {
    1: "DRT",
    2: "DDT",
    3: "FDR",
    4: "RTD",
    5: "RDT",
    6: "AEX",
    7: "DRH",
    8: "ADH",
    9: "DAS",
    10: "SVR",
    11: "SGT",
    12: "AGT",
    13: "SPN",
    14: "IRT",
    15: "PBT",
    16: "ATR",
    17: "WMB",
    18: "RTR"
}


CODETOFULL = {
    "DRT": "FAA Director",
    "DDT": "FAA Deputy Director",
    "FDR": "Server Founder",
    "RTD": "Retired Director",
    "RDT": "Retired Deputy Director",
    "AEX": "Agency Executive",
    "DRH": "Department Head",
    "ADH": "Acting Department Dead",
    "DAS": "Department Assistant",
    "SVR": "Department Supervisor",
    "SGT": "Senior Special Agent",
    "AGT": "Special Agent",
    "SPN": "Suspended",
    "IRT": "In Re-Training",
    "PBT": "Probationary Agent",
    "ATR": "Agent Trainee",
    "WMB": "Wumbo",
    "RTR": "Honourable Discharge"
}

# ON READY ========================================================================

@bot.event
async def on_connect():
    global guild, cguild
    print(f'[PYCORD] Bot Login Username: {bot.user}')
    try:
        guild = await bot.fetch_guild(GUILDID)
        cguild = bot.get_guild(GUILDID)
        if guild:
            print(f'[PYCORD] Connected to guild: {guild.name}')
            print("[PYCORD] Trying to sync commands...")
            await bot.sync_commands()
            print("[PYCORD] Bot commands synced")
            
        else:
            print("[ERROR] Guild not found.")
    except Exception as e:
        print(f"[ERROR] Failed to connect, sync and run vital self-check: {e}")

# @bot.command(description="Get discord time from Unix time or datetime selection.")
# def hammertime(ctx, day: int, month: int, year:int,)

# SETUP ========================================================================
@setup.command(description="Add agent to staff list.")
@commands.has_any_role("Department Head", "Department Supervisor")
async def addagent(ctx, user: discord.User, name: str, rank: str):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        embed = discord.Embed(title = "Agent Already Exists",
                              description = "The agent has not been added due to the agent already being inside the database.")
        embed.add_field(name = "Agent ID", value = str(user.id))
        await ctx.respond(embed=embed)
        return
    else:
        if rank.upper() in CODETORANK:
            intrank = CODETORANK[rank.upper()]
        else:
            embed = discord.Embed(title = "Rank Doesn't Exist",
                                    description = "The agent has not been added because the rank does not exist.")
            embed.add_field(name = "rank", value = rank.upper())
            await ctx.respond(embed=embed)
            return
        cursor.execute('INSERT OR REPLACE INTO staff (userid, name, rank, fi, fione, fitwo, fithree) VALUES (?, ?, ?, ?, ?, ?, ?)', (user.id, name, intrank, 0, "", "", ""))
        dbcon.commit()
        role = discord.utils.get(ctx.guild.roles, name=CODETOFULL[rank.upper()])
        await user.add_roles(role)
        role = discord.utils.get(ctx.guild.roles, name="FAA Employees")
        await user.add_roles(role)
        embed = discord.Embed(title = "Agent Added Successfully!")
        embed.add_field(name = "Agent Name", value = name, inline = True)
        embed.add_field(name = "Rank", value = rank.upper(), inline = True)
        embed.add_field(name = "Agent ID", value = user.id, inline = True)
        await ctx.respond(embed=embed)

# HR PROMOTE / DEMOTE  ============================================================
@exec.command(description="Promote an agent.")
@commands.has_any_role("Human Resources Department")
async def promote(ctx, user: discord.User, rank: str):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        if rank.upper() in CODETORANK:
            intrank = CODETORANK[rank.upper()]
        else:
            embed = discord.Embed(title = "Rank Doesn't Exist",
                                    description = "The agent has not been promoted because the rank does not exist.")
            embed.add_field(name = "rank", value = rank.upper())
            await ctx.respond(embed=embed)
            return
        
        cursor.execute("""
SELECT rank
FROM staff
WHERE userid = ?
""", (user.id,))
        currentrank = cursor.fetchone()

        if currentrank[0] < intrank:
            embed = discord.Embed(title = "Not a Promotion")
            await ctx.respond(embed=embed)
            return

        rankrole = discord.utils.get(ctx.guild.roles, name=CODETOFULL[RANKTOCODE[currentrank[0]]])
        cursor.execute('''
            UPDATE staff
            SET rank = ?
            WHERE userid = ?
        ''', (intrank, user.id))


        dbcon.commit()
        role = discord.utils.get(ctx.guild.roles, name=CODETOFULL[rank.upper()])
        
        await user.remove_roles(rankrole)
        await user.add_roles(role)
        
        embed = discord.Embed(title="Promoted Agent")
        embed.add_field(name="Username", value=user.display_name)
        embed.add_field(name="User ID", value=user.id)
        embed.add_field(name="Previous Rank", value=CODETOFULL[RANKTOCODE[currentrank[0]]])
        embed.add_field(name="Current Rank", value=CODETOFULL[RANKTOCODE[intrank]])
        embed.add_field(name="Done By", value=ctx.user.display_name)
        embed.add_field(name="Done By", value=ctx.user.id)
    
        channel = bot.get_channel(1327463694958989412)
        staff_updates = bot.get_channel(1153067498304974928)
        
        await staff_updates.send(f"<@{user.id}>", embed=embed)
        
        await channel.send(embed=embed)
        await ctx.respond(embed=embed)

@exec.command(description="Demote an agent.")
@commands.has_any_role("Human Resources Department")
async def demote(ctx, user: discord.User, rank: str):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
SELECT rank
FROM staff
WHERE userid = ?
""", (user.id,))
        currentrank = cursor.fetchone()
        
        if rank.upper() in CODETORANK:
            intrank = CODETORANK[rank.upper()]
        elif rank.upper() == "MBR":
            roles = user.roles
            
            for role in roles[1:]:
                await user.remove_roles(role)
            memberrole = discord.utils.get(ctx.guild.roles, name="Member")
            await user.add_roles(memberrole)
            
            cursor.execute(f"DELETE FROM staff WHERE userid = {user.id}")
            cursor.execute(f"DELETE FROM humanresources WHERE userid = {user.id}")
            cursor.execute(f"DELETE FROM publicaffairs WHERE userid = {user.id}")
            cursor.execute(f"DELETE FROM qdtrainers WHERE userid = {user.id}")
            
            dbcon.commit()
            
            embed = discord.Embed(title="Removed and Demoted Agent")
            embed.add_field(name="Username", value=user.display_name)
            embed.add_field(name="User ID", value=user.id)
            embed.add_field(name="Previous Rank", value=CODETOFULL[RANKTOCODE[currentrank[0]]])
            embed.add_field(name="Current Rank", value="Member (No Longer Staff)")
            embed.add_field(name="Done By", value=ctx.user.display_name)
            embed.add_field(name="Done By", value=ctx.user.id)
        
            channel = bot.get_channel(1327463694958989412)
            staff_updates = bot.get_channel(1153067498304974928)
        
            await staff_updates.send(f"<@{user.id}>", embed=embed)
            
            await channel.send(embed=embed)
            await ctx.respond(embed=embed)
            return
        else:
            embed = discord.Embed(title = "Rank Doesn't Exist",
                                    description = "The agent has not been added because the rank does not exist.")
            embed.add_field(name = "rank", value = rank.upper())
            await ctx.respond(embed=embed)
            return

        if currentrank[0] > intrank:
            embed = discord.Embed(title = "Not a Demotion")
            await ctx.respond(embed=embed)
            return

        rankrole = discord.utils.get(ctx.guild.roles, name=CODETOFULL[RANKTOCODE[currentrank[0]]])
        cursor.execute('''
            UPDATE staff
            SET rank = ?
            WHERE userid = ?
        ''', (intrank, user.id))


        dbcon.commit()
        role = discord.utils.get(ctx.guild.roles, name=CODETOFULL[rank.upper()])
        
        await user.remove_roles(rankrole)
        await user.add_roles(role)
        
        embed = discord.Embed(title="Demoted Agent")
        embed.add_field(name="Username", value=user.display_name)
        embed.add_field(name="User ID", value=user.id)
        embed.add_field(name="Previous Rank", value=CODETOFULL[RANKTOCODE[currentrank[0]]])
        embed.add_field(name="Current Rank", value=CODETOFULL[RANKTOCODE[intrank]])
        embed.add_field(name="Done By", value=ctx.user.display_name)
        embed.add_field(name="Done By", value=ctx.user.id)
    
        channel = bot.get_channel(1327463694958989412)
        staff_updates = bot.get_channel(1153067498304974928)
        
        await staff_updates.send(f"<@{user.id}>", embed=embed)
        
        await channel.send(embed=embed)
        await ctx.respond(embed=embed)

# PAD SETUP ================================================================================================
@setup.command(description="Add a PAD agent into the Public Affairs table in FAA SQLite database.")
@commands.has_any_role("Department Head", "Department Supervisor")
async def addpadagent(ctx, user: discord.User):
    cursor.execute("SELECT * FROM publicaffairs WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        embed = discord.Embed(title = "Agent Already Exists",
                              description = "The agent has not been added due to the agent already being inside the database.")
        embed.add_field(name = "Agent ID", value = str(user.id))
        embed.add_field(name = "Error", value = "PADDBError: Sqlite3: FetchReturnsRowType")
        await ctx.respond(embed=embed)
        return
    cursor.execute('INSERT OR REPLACE INTO publicaffairs (userid, reports, inquiries, events) VALUES (?, ?, ?, ?)', (user.id, 0, 0, 0))
    dbcon.commit()
    embed = discord.Embed(title = "PA-D: Agent Added Successfully!")
    embed.add_field(name = "Agent ID", value = str(user.id), inline = True)
    await ctx.respond(embed=embed)
    
@setup.command(description="Remove a PAD agent from the Public Affiars table in the FAA SQLite database.")
async def removepadagent(ctx, user:discord.User):
    cursor.execute("SELECT * FROM publicaffairs WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM publicaffairs WHERE userid = ?", (user.id,))
        embed = discord.Embed(title = "PA-D: Agent Removed Successfully!")
        embed.add_field(name = "Removed Agent's ID", value = str(user.id), inline = True)
    else:
        embed = discord.Embed(title = "PA-D: No such user in the database")
        embed.add_field(name = "User ID Tried", value=str(user.id))      
    await ctx.respond(embed=embed)

# HRD SETUP

@setup.command(description="Add a HRD agent into the Human Resources table in FAA SQLite database.")
@commands.has_any_role("Department Head", "Department Supervisor")
async def addhrdagent(ctx, user: discord.User):
    cursor.execute("SELECT * FROM humanresources WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        embed = discord.Embed(title = "Agent Already Exists",
                              description = "The agent has not been added due to the agent already being inside the database.")
        embed.add_field(name = "Agent ID", value = str(user.id))
        embed.add_field(name = "Error", value = "HRDDBError: Sqlite3: FetchReturnsRowType")
        await ctx.respond(embed=embed)
        return
    cursor.execute('INSERT OR REPLACE INTO humanresources (userid, interviews) VALUES (?, ?)', (user.id, 0))
    dbcon.commit()
    embed = discord.Embed(title = "HR-D: Agent Added Successfully!")
    embed.add_field(name = "Agent ID", value = str(user.id), inline = True)
    await ctx.respond(embed=embed)
    
@setup.command(description="Remove a HRD agent from the Human Resources Table in the FAA SQLite database.")
async def removehrdagent(ctx, user:discord.User):
    cursor.execute("SELECT * FROM humanresources WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM humanresources WHERE userid = ?", (user.id,))
        dbcon.commit()
        embed = discord.Embed(title = "HR-D: Agent Removed Successfully!")
        embed.add_field(name = "Removed Agent's ID", value = str(user.id), inline = True)
    else:
        embed = discord.Embed(title = "HR-D: No such user in the database")
        embed.add_field(name = "User ID Tried", value=str(user.id))      
    await ctx.respond(embed=embed)   

# ============ PUBLIC AFFAIRS DEPARTMENT ============
# ========================================================================================================================
@pad.command(description="Log a report.")
@commands.has_any_role("Public Affairs Department")
async def logreport(ctx):
    cursor.execute("SELECT * FROM publicaffairs WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Public Affairs Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "PADDBError: Sqlite3: FetchReturnsNull")
        ctx.respond(embed=embed)
        return
    cursor.execute("INSERT OR REPLACE INTO publicaffairs (userid, reports, inquiries, events) VALUES (?, ?, ?, ?)", (ctx.user.id, row[1]+1, row[2], row[3]))
    dbcon.commit()
    
    embed = discord.Embed(title = "PA-D: Report Logged")
    embed.add_field(name = "Current reports:", value = row[1]+1)
    
    channel = bot.get_channel(1327463288954425488)
    
    logembed = discord.Embed(title = f"{ctx.user.display_name} ({ctx.user.id}) - Public Affairs Log")
    logembed.add_field(name = "Reports", value = row[1]+1)
    logembed.add_field(name = "Inquries", value = row[2])
    logembed.add_field(name = "Events", value = row[3])
    
    await channel.send(embed=logembed)
    await ctx.respond(embed=embed)
        

@pad.command(description="Log an inquiry.")
@commands.has_any_role("Public Affairs Department")
async def loginquiry(ctx):
    cursor.execute("SELECT * FROM publicaffairs WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Public Affairs Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "PADDBError: Sqlite3: FetchReturnsNull")
        ctx.respond(embed=embed)
        return
    cursor.execute("INSERT OR REPLACE INTO publicaffairs (userid, reports, inquiries, events) VALUES (?, ?, ?, ?)", (ctx.user.id, row[1], row[2]+1, row[3]))
    dbcon.commit()
    embed = discord.Embed(title = "PA-D: Inquiry Logged")
    embed.add_field(name = "Current inquiries:", value = row[2]+1)
    
    channel = bot.get_channel(1327463288954425488)
    
    logembed = discord.Embed(title = f"{ctx.user.display_name} ({ctx.user.id}) - Public Affairs Log")
    logembed.add_field(name = "Reports", value = row[1])
    logembed.add_field(name = "Inquries", value = row[2]+1)
    logembed.add_field(name = "Events", value = row[3])
    
    await channel.send(embed=logembed)
    await ctx.respond(embed=embed)

@pad.command(description="Log an event.")
@commands.has_any_role("Public Affairs Department")
async def logevent(ctx):
    cursor.execute("SELECT * FROM publicaffairs WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Public Affairs Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "PADDBError: Sqlite3: FetchReturnsNull")
        ctx.respond(embed=embed)
        return
    cursor.execute("INSERT OR REPLACE INTO publicaffairs (userid, reports, inquiries, events) VALUES (?, ?, ?, ?)", (ctx.user.id, row[1], row[2], row[3]+1))
    dbcon.commit()
    embed = discord.Embed(title = "PA-D: Event Logged")
    embed.add_field(name = "Current events:", value = row[3]+1)
    
    channel = bot.get_channel(1327463288954425488)
    
    logembed = discord.Embed(title = f"{ctx.user.display_name} ({ctx.user.id}) - Public Affairs Log")
    logembed.add_field(name = "Reports", value = row[1])
    logembed.add_field(name = "Inquries", value = row[2])
    logembed.add_field(name = "Events", value = row[3]+1)
    
    await channel.send(embed=logembed)
    await ctx.respond(embed=embed)

# ==================================== HRD RESET REI ============================================================

class HRDPADResetREIView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.confirmed = False

    @discord.ui.button(label="Reset REIs", style=discord.ButtonStyle.danger)
    async def reset_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction): 
        if not self.confirmed:
            await interaction.response.edit_message(content="Are you sure you want to reset reports, inquiries, and events? This action cannot be undone. Click 'Reset REIs' again to confirm.", view=self)
            self.confirmed = True 
        else:
            desc = ""
            cursor.execute("SELECT * FROM PUBLICAFFAIRS")  # Corrected query
            rows = cursor.fetchall()
            for row in rows:
                user = cguild.get_member(row[0])
                desc += f"{user.display_name} - {row[1]} / {row[2]} / {row[3]}\n"
            # Resetting all records:
            for row in rows: 
                cursor.execute("UPDATE PUBLICAFFAIRS SET reports = 0, inquiries = 0, events = 0 WHERE userid = ?", (row[0],))
            desc += f"\nRan by {interaction.user.display_name}"
            ch = bot.get_channel(1327463288954425488)
    
            await ch.send(embed=discord.Embed(title="GRADING PERIOD RESET"))
            
            embed = discord.Embed(title="Current Grading Period - Roundup - Public Affairs", description=desc)
            await interaction.response.edit_message(content="", embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.edit_message(content="Cancelled.", view=None)


@exec.command(description="Reset all Reports / Inquriries / Events for the week or subdivision of the month.")
async def resethrdinterviews(ctx):
    cursor.execute("SELECT * FROM humanresources")
    row = cursor.fetchall()
    if not row:
        embed = discord.Embed(title = "HR-D: Reset HRD Interviews: Error", color=discord.Color.red, description="No one is in the database.")
        embed.add_field(name = "Error code", value = "HRDDBError: Sqlite3: FetchAllReturnsNull")
        await ctx.respond(embed=embed)
        return
    else:
        view = HRDIntResetREIView()
        await ctx.respond("Confirm Reset?", view=view)    

@hrd.command(description="Log an interview.")
async def loginterview(ctx):
    cursor.execute("SELECT * FROM humanresources WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Human Resources Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        await embed.add_field(name = "Error", value = "HRDDBError: Sqlite3: FetchReturnsNull")
        ctx.respond(embed=embed)
        return
    cursor.execute("INSERT OR REPLACE INTO humanresources (userid, interviews) VALUES (?, ?)", (ctx.user.id, row[1]+1))
    dbcon.commit()
    
    embed = discord.Embed(title = "HR-D: Interview Logged")
    embed.add_field(name = "Current interviews:", value = row[1] + 1)
    
    channel = bot.get_channel(1327463694958989412)
    
    logembed = discord.Embed(title = f"{ctx.user.display_name} ({ctx.user.id}) - Human Resources Log")
    logembed.add_field(name = "Interview", value = row[1] + 1)
    logembed.add_field(name = "Channel", value = ctx.channel.name)
    
    await channel.send(embed=logembed)
    await ctx.respond(embed=embed)

@exec.command(description="Give a staff member a False Interaction Inferaction.")
async def logfi(ctx, user: discord.User, reason: str):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Human Resources Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "HRDDBError: Sqlite3: FetchReturnsNull")
        await ctx.respond(embed=embed)
        return
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    
    if not row:
        embed = discord.Embed(title="User not in staff list")
        await ctx.respond(embed=embed)
        return
    if row[6]:
        embed = discord.Embed(title="WARNING: FI NOT LOGGED", description="The staff user inputted has three FalseInteraction Inferactions. Please demote or terminate this user accordingly.")
        embed.add_field(name="Error/debug log (TD only)", value="FAAUtilityBot.database.sql.errors.userinjectederrors.FalseInteractionStrikeCounterMet")
        await ctx.respond(embed=embed)
        return
    
    if not row[4]:
        cursor.execute("INSERT OR REPLACE INTO staff (userid, name, rank, fi, fione, fitwo, fithree) VALUES (?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], row[3]+1, reason, None, None))
    elif not row[5]:
        cursor.execute("INSERT OR REPLACE INTO staff (userid, name, rank, fi, fione, fitwo, fithree) VALUES (?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], row[3]+1, row[4], reason, None))
    elif not row[6]:
        cursor.execute("INSERT OR REPLACE INTO staff (userid, name, rank, fi, fione, fitwo, fithree) VALUES (?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], row[3]+1, row[4], row[5], reason))
    
    dbcon.commit()
    
    embed = discord.Embed(title="FalseInteraction Inferation Logged")
    embed.add_field(name="User ID:", value=user.id)
    embed.add_field(name="Username:", value=user.name)
    embed.add_field(name="Server Specific Display Name:", value=user.display_name)
    embed.add_field(name="Total FIs:", value=row[3]+1)
    embed.add_field(name="Done By", value=ctx.user.id)
    
    channel = bot.get_channel(1327463694958989412)
    
    await channel.send("falseinteractionfaautils", embed=embed)
    
    await ctx.respond("TD only: debug tag falseinteractionfaautils (Non TD please ignore, this behavior is expected)", embed=embed)

@exec.command(description="Remove all FalseInteractions. This is for executives (DRH+) ONLY.")
async def clearfi(ctx, user: discord.User):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Human Resources Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "HRDDBError: Sqlite3: FetchReturnsNull")
        await ctx.respond(embed=embed)
        return
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    
    if not row:
        embed = discord.Embed(title="User not in staff list")
        await ctx.respond(embed=embed)
        return
    
    cursor.execute("INSERT OR REPLACE INTO staff (userid, name, rank, fi, fione, fitwo, fithree) VALUES (?, ?, ?, ?, ?, ?, ?)", (row[0], row[1], row[2], 0, None, None, None))
    
    embed = discord.Embed(title="FalseInteraction Inferactions Cleared")
    embed.add_field(name="FI1", value=row[4])
    embed.add_field(name="FI2", value=row[5])
    embed.add_field(name="FI3", value=row[6])
    embed.add_field(name="Total FI Count", value=row[3])
    embed.add_field(name="User ID", value=user.id)
    embed.add_field(name="Done By", value=ctx.user.id)
    
    channel = bot.get_channel(1327463694958989412)
    
    await channel.send("falseinteractionclear", embed=embed)
    await ctx.respond(embed=embed)

@hrd.command(description="Get all FIs from one user.")
async def getfi(ctx, user: discord.User):
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (ctx.user.id,))
    row = cursor.fetchone()
    if not row:
        embed = discord.embed(title = "You are not in the Human Resources Department!",
                              description = "If you think this is a mistake, ask your supervisor.")
        embed.add_field(name = "Error", value = "HRDDBError: Sqlite3: FetchReturnsNull")
        await ctx.respond(embed=embed)
        return
    cursor.execute("SELECT * FROM staff WHERE userid = ?", (user.id,))
    row = cursor.fetchone()
    
    if not row:
        embed = discord.Embed(title="User not in staff list")
        await ctx.respond(embed=embed)
        return

    embed = discord.Embed(title="FalseInteraction Inferactions List")
    embed.add_field(name="FI1", value=row[4])
    embed.add_field(name="FI2", value=row[5])
    embed.add_field(name="FI3", value=row[6])
    embed.add_field(name="Total FI Count", value=row[3])
    embed.add_field(name="User ID", value=user.id)
    
    await ctx.respond(embed=embed)
class HRDIntResetREIView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.confirmed = False

    @discord.ui.button(label="Reset Interviews", style=discord.ButtonStyle.danger)
    async def reset_button_callback(self, button: discord.ui.Button, interaction: discord.Interaction): 
        if not self.confirmed:
            await interaction.response.edit_message(content="Are you sure you want to reset interviews? This action cannot be undone. Click 'Reset Interviews' again to confirm.", view=self)
            self.confirmed = True 
        else:
            desc = ""
            cursor.execute("SELECT * FROM humanresources")  # Corrected query
            rows = cursor.fetchall()
            for row in rows:
                user = cguild.get_member(row[0])
                desc += f"{user.display_name} - {row[0]}\n"
            
            # Resetting all records:
            for row in rows: 
                cursor.execute("UPDATE humanresources SET interviews = 0 WHERE userid = ?", (row[0],))
            desc += f"\nRan by {interaction.user.display_name}"
            
            ch = bot.get_channel(1327463694958989412)
    
            await ch.send(embed=discord.Embed(title="GRADING PERIOD RESET"))
            
            embed = discord.Embed(title="Current Grading Period - Roundup - Human Resources", description=desc)
            await interaction.response.edit_message(content="", embed=embed, view=None)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.primary)
    async def cancel_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button): 
        await interaction.response.edit_message(content="Cancelled.", view=None)


@exec.command(description="Reset all Reports / Inquriries / Events for the week or subdivision of the month.")
async def resetpadrei(ctx):
    cursor.execute("SELECT * FROM PUBLICAFFAIRS")
    row = cursor.fetchall()
    if not row:
        embed = discord.Embed(title = "HR-D: Reset PA-D R/E/Is: Error", color=discord.Color.red, description="No one is in the database.")
        embed.add_field(name = "Error code", value = "PADDBError: Sqlite3: FetchAllReturnsNull")
        await ctx.respond(embed=embed)
        return
    else:
        view = HRDPADResetREIView()
        await ctx.respond("Confirm Reset?", view=view)    

bot.run(TOKEN)