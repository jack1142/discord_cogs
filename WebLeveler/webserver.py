from aiohttp import web
import asyncio
import os
from shutil import copyfile
import discord

class WebServer:

    def __init__(self, bot):
        self.app = web.Application()
        self.bot = bot
        self.port = 6969
        self.handler = None
        self.runner = None
        self.site = None
        self.div = ""
        self.body = None

    def __unload(self):
        self.bot.loop.create_task(self.runner.cleanup())

    def get_body(self, path):
        if self.body is None:
            folder = path[0]
            basic = os.path.join(folder, "index.html")
            body = open(basic, "r", encoding="utf-8").read()
            self.body = body
            return self.body
        else:
            return self.body

    async def make_webserver(self, path):
        cog = self.bot.get_cog("Leveler")
        stats = cog.profiles
        async def page(request):
            data = {}
            res = "<p id='datadiv'>"
            for i in self.bot.guilds:
                data[i.id] = {}
                data[i.id] = await stats._get_leaderboard(i)
            for i in data:
                res += "<h3>Serveur: " + self.bot.get_guild(i).name + "</h3><br />"
                for j in data[i]:
                    user = self.bot.get_user(j["id"])
                    userxp = j["xp"]
                    userlevel = j["lvl"]
                    res += f"{user.display_name}: Niveau {userlevel} avec {userxp} XP !<br />"
                res += "</p><br /><p id='datadiv'>"
            res += "</p>"
            body = self.get_body(path)
            body = body.replace("[[]]", res)
            body = body.replace("<div id='DataContainer' style='display: none'>", "<div id='DataContainer' style='display: inline-block'>")
            self.body = body
            return web.Response(text=body, content_type='text/html')

        async def userinfo(request):
            data = await request.post()
            body = self.get_body(path)
            usr = data["user"]
            srch = discord.utils.get(self.bot.get_all_members(), name=usr)
            if srch is None:
                srch = discord.utils.get(self.bot.get_all_members(), id=int(usr))
            if srch is None:
                res = "Utilisateur inconnu"
            else:
                info = await cog.profile_data(srch)
                xp = info["xp"]
                nxp = info["nxp"]
                lvl = info["lvl"]
                ldb = info["ldb"]
                desc = info["desc"]
                roles = await stats._get_guild_roles(srch.guild)
                ln = lvl // 10
                if ln == 0 or len(roles) == 0:
                    elo = "Nouveau"
                elif ln > len(roles):
                    relo = roles[len(roles)-1]
                    elo = srch.guild.get_role(relo).name
                else:
                    relo = roles[ln-1]
                    elo = srch.guild.get_role(relo).name
                res = f"<p><br />Niveau: {lvl}<br />Exp: {xp} / {nxp}<br />Elo: {elo}<br />Classement: {ldb+1}<br /><br />{desc}</p>"
                body = body.replace("<div id='dialog' style='display: none'>", f"<div id='dialog' title={srch.display_name} style='display: none'>")
                body = body.replace("(())", res)
                body = body.replace("<div id='dialog' style='display: none'>", "<div id='dialog' style='display: inline-block'>")
                self.body = body
                return web.Response(text=body, content_type='text/html')
            body = body.replace("(())", res)
            self.body = body
            return web.Response(text=body, content_type='text/html')

        await asyncio.sleep(3)
        self.app.router.add_get('/', page)
        self.app.router.add_post('/', userinfo)
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.handler = self.app.make_handler(debug=True)
        self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
        await self.site.start()
        print('WebTest started ...')