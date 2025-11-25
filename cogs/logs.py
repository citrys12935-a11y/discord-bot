import discord
from discord.ext import commands
from datetime import datetime
import asyncio

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        from utils.database import Database
        self.db = Database()

    async def get_log_channel(self, guild_id):
        settings = self.db.get_server_settings(guild_id)
        if not settings[9]:  # logs_enabled
            return None
        
        channel_id = settings[10]  # log_channel_id
        if not channel_id:
            return None
        
        channel = self.bot.get_channel(channel_id)
        return channel

    async def send_log(self, guild, embed):
        channel = await self.get_log_channel(guild.id)
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

    # Логирование ролей
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """Логирование создания роли"""
        embed = discord.Embed(
            title="🎭 Создана новая роль",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Роль", value=role.mention, inline=True)
        embed.add_field(name="Название", value=role.name, inline=True)
        embed.add_field(name="Цвет", value=str(role.color), inline=True)
        embed.add_field(name="Позиция", value=role.position, inline=True)
        embed.add_field(name="Упоминаемая", value="Да" if role.mentionable else "Нет", inline=True)
        embed.add_field(name="Отдельно показываемая", value="Да" if role.hoist else "Нет", inline=True)
        
        # Получаем информацию о том, кто создал роль из аудит-лога
        try:
            async for entry in role.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    embed.add_field(name="Создатель", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Логирование удаления роли"""
        embed = discord.Embed(
            title="🎭 Удалена роль",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Название", value=role.name, inline=True)
        embed.add_field(name="Цвет", value=str(role.color), inline=True)
        embed.add_field(name="Позиция", value=role.position, inline=True)
        
        # Получаем информацию о том, кто удалил роль из аудит-лога
        try:
            async for entry in role.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    embed.add_field(name="Удалил", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """Логирование изменений роли"""
        changes = []
        
        # Проверяем изменения имени
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
        
        # Проверяем изменения цвета
        if before.color != after.color:
            changes.append(f"**Цвет:** {before.color} → {after.color}")
        
        # Проверяем изменения разрешений
        if before.permissions != after.permissions:
            changed_perms = []
            for perm, value in before.permissions:
                new_value = getattr(after.permissions, perm)
                if value != new_value:
                    perm_name = perm.replace('_', ' ').title()
                    changed_perms.append(f"{perm_name}: {'✅' if new_value else '❌'}")
            
            if changed_perms:
                changes.append("**Разрешения:** " + ", ".join(changed_perms))
        
        # Проверяем изменения позиции
        if before.position != after.position:
            changes.append(f"**Позиция:** {before.position} → {after.position}")
        
        # Проверяем изменения mentionable
        if before.mentionable != after.mentionable:
            changes.append(f"**Упоминаемая:** {'Да' if after.mentionable else 'Нет'}")
        
        # Проверяем изменения hoist
        if before.hoist != after.hoist:
            changes.append(f"**Отдельно показываемая:** {'Да' if after.hoist else 'Нет'}")
        
        # Если есть изменения, создаем embed
        if changes:
            embed = discord.Embed(
                title="🎭 Изменена роль",
                color=0xf39c12,
                timestamp=datetime.now()
            )
            embed.add_field(name="Роль", value=after.mention, inline=True)
            embed.add_field(name="Изменения", value="\n".join(changes), inline=False)
            
            # Получаем информацию о том, кто изменил роль из аудит-лога
            try:
                async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id:
                        embed.add_field(name="Изменил", value=entry.user.mention, inline=True)
                        break
            except:
                pass
                
            await self.send_log(after.guild, embed)

    # Расширенное логирование каналов
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        embed = discord.Embed(
            title="📁 Создан канал",
            description=f"Канал: {channel.mention}",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Тип", value=self.get_channel_type_name(channel.type), inline=True)
        embed.add_field(name="Категория", value=channel.category.name if channel.category else "Нет", inline=True)
        
        # Дополнительная информация в зависимости от типа канала
        if isinstance(channel, discord.TextChannel):
            embed.add_field(name="NSFW", value="Да" if channel.is_nsfw() else "Нет", inline=True)
            embed.add_field(name="Медленный режим", value=f"{channel.slowmode_delay} сек" if channel.slowmode_delay else "Нет", inline=True)
        elif isinstance(channel, discord.VoiceChannel):
            embed.add_field(name="Лимит пользователей", value=channel.user_limit if channel.user_limit else "Безлимит", inline=True)
            embed.add_field(name="Битрейт", value=f"{channel.bitrate//1000} kbps", inline=True)
        
        # Получаем информацию о том, кто создал канал из аудит-лога
        try:
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    embed.add_field(name="Создатель", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        embed = discord.Embed(
            title="🗑️ Удален канал",
            description=f"Канал: {channel.name}",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Тип", value=self.get_channel_type_name(channel.type), inline=True)
        embed.add_field(name="Категория", value=channel.category.name if channel.category else "Нет", inline=True)
        
        # Получаем информацию о том, кто удалил канал из аудит-лога
        try:
            async for entry in channel.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    embed.add_field(name="Удалил", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        changes = []
        
        # Проверяем изменения имени
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
        
        # Проверяем изменения категории
        if before.category != after.category:
            before_category = before.category.name if before.category else "Нет"
            after_category = after.category.name if after.category else "Нет"
            changes.append(f"**Категория:** {before_category} → {after_category}")
        
        # Проверяем изменения позиции
        if before.position != after.position:
            changes.append(f"**Позиция:** {before.position} → {after.position}")
        
        # Дополнительные проверки для текстовых каналов
        if isinstance(before, discord.TextChannel) and isinstance(after, discord.TextChannel):
            if before.topic != after.topic:
                before_topic = before.topic[:50] + "..." if before.topic and len(before.topic) > 50 else before.topic or "Нет"
                after_topic = after.topic[:50] + "..." if after.topic and len(after.topic) > 50 else after.topic or "Нет"
                changes.append(f"**Тема:** {before_topic} → {after_topic}")
            
            if before.is_nsfw() != after.is_nsfw():
                changes.append(f"**NSFW:** {'Да' if after.is_nsfw() else 'Нет'}")
            
            if before.slowmode_delay != after.slowmode_delay:
                before_delay = f"{before.slowmode_delay} сек" if before.slowmode_delay else "Нет"
                after_delay = f"{after.slowmode_delay} сек" if after.slowmode_delay else "Нет"
                changes.append(f"**Медленный режим:** {before_delay} → {after_delay}")
        
        # Дополнительные проверки для голосовых каналов
        if isinstance(before, discord.VoiceChannel) and isinstance(after, discord.VoiceChannel):
            if before.bitrate != after.bitrate:
                changes.append(f"**Битрейт:** {before.bitrate//1000} → {after.bitrate//1000} kbps")
            
            if before.user_limit != after.user_limit:
                before_limit = before.user_limit if before.user_limit else "Безлимит"
                after_limit = after.user_limit if after.user_limit else "Безлимит"
                changes.append(f"**Лимит пользователей:** {before_limit} → {after_limit}")
        
        # Проверяем изменения разрешений
        if before.overwrites != after.overwrites:
            # Сравниваем overwrites для поиска изменений
            all_targets = set(before.overwrites.keys()) | set(after.overwrites.keys())
            permission_changes = []
            
            for target in all_targets:
                before_overwrite = before.overwrites.get(target)
                after_overwrite = after.overwrites.get(target)
                
                if before_overwrite != after_overwrite:
                    target_name = target.mention if isinstance(target, (discord.Member, discord.Role)) else target.name
                    permission_changes.append(target_name)
            
            if permission_changes:
                changes.append(f"**Изменены права для:** {', '.join(permission_changes[:3])}" + ("..." if len(permission_changes) > 3 else ""))
        
        # Если есть изменения, создаем embed
        if changes:
            embed = discord.Embed(
                title="✏️ Изменен канал",
                description=f"Канал: {after.mention}",
                color=0xf39c12,
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes), inline=False)
            
            # Получаем информацию о том, кто изменил канал из аудит-лога
            try:
                async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_update):
                    if entry.target.id == after.id:
                        embed.add_field(name="Изменил", value=entry.user.mention, inline=True)
                        break
            except:
                pass
                
            await self.send_log(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_pins_update(self, channel, last_pin):
        """Логирование обновления закрепленных сообщений"""
        embed = discord.Embed(
            title="📌 Обновлены закрепленные сообщения",
            description=f"Канал: {channel.mention}",
            color=0x3498db,
            timestamp=datetime.now()
        )
        
        pins = await channel.pins()
        embed.add_field(name="Количество закрепленных", value=len(pins), inline=True)
        
        await self.send_log(channel.guild, embed)

    # Логирование категорий каналов
    @commands.Cog.listener()
    async def on_guild_category_create(self, category):
        embed = discord.Embed(
            title="📂 Создана категория",
            description=f"Категория: {category.name}",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Позиция", value=category.position, inline=True)
        
        try:
            async for entry in category.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_create):
                if entry.target.id == category.id:
                    embed.add_field(name="Создатель", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(category.guild, embed)

    @commands.Cog.listener()
    async def on_guild_category_delete(self, category):
        embed = discord.Embed(
            title="🗑️ Удалена категория",
            description=f"Категория: {category.name}",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Позиция", value=category.position, inline=True)
        
        try:
            async for entry in category.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == category.id:
                    embed.add_field(name="Удалил", value=entry.user.mention, inline=True)
                    break
        except:
            pass
            
        await self.send_log(category.guild, embed)

    @commands.Cog.listener()
    async def on_guild_category_update(self, before, after):
        changes = []
        
        if before.name != after.name:
            changes.append(f"**Название:** {before.name} → {after.name}")
        
        if before.position != after.position:
            changes.append(f"**Позиция:** {before.position} → {after.position}")
        
        if changes:
            embed = discord.Embed(
                title="✏️ Изменена категория",
                description=f"Категория: {after.name}",
                color=0xf39c12,
                timestamp=datetime.now()
            )
            embed.add_field(name="Изменения", value="\n".join(changes), inline=False)
            
            try:
                async for entry in after.guild.audit_logs(limit=5, action=discord.AuditLogAction.channel_update):
                    if entry.target.id == after.id:
                        embed.add_field(name="Изменил", value=entry.user.mention, inline=True)
                        break
            except:
                pass
                
            await self.send_log(after.guild, embed)

    # Вспомогательные методы
    def get_channel_type_name(self, channel_type):
        type_names = {
            discord.ChannelType.text: "📝 Текстовый",
            discord.ChannelType.voice: "🔊 Голосовой",
            discord.ChannelType.category: "📂 Категория",
            discord.ChannelType.news: "📢 Новостной",
            discord.ChannelType.stage_voice: "🎤 Стейдж",
            discord.ChannelType.forum: "💬 Форум"
        }
        return type_names.get(channel_type, str(channel_type).title())

    # События магазина и торговой площадки (из вашего кода)
    @commands.Cog.listener()
    async def on_shop_purchase(self, ctx, item, price):
        """Логирование покупки в магазине"""
        embed = discord.Embed(
            title="🛍️ Покупка в магазине",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Покупатель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Предмет", value=item[2], inline=True)
        embed.add_field(name="Цена", value=f"{price} монет", inline=True)
        embed.add_field(name="ID предмета", value=item[0], inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener() 
    async def on_shop_item_add(self, ctx, item_id, name, price, item_type):
        """Логирование добавления предмета в магазин"""
        embed = discord.Embed(
            title="🛍️ Добавлен предмет в магазин",
            color=0x3498db,
            timestamp=datetime.now()
        )
        embed.add_field(name="Администратор", value=ctx.author.mention, inline=True)
        embed.add_field(name="Предмет", value=name, inline=True)
        embed.add_field(name="Цена", value=f"{price} монет", inline=True)
        embed.add_field(name="Тип", value=item_type, inline=True)
        embed.add_field(name="ID", value=item_id, inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_shop_item_remove(self, ctx, item_id, name):
        """Логирование удаления предмета из магазина"""
        embed = discord.Embed(
            title="🛍️ Удален предмет из магазина",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Администратор", value=ctx.author.mention, inline=True)
        embed.add_field(name="Предмет", value=name, inline=True)
        embed.add_field(name="ID", value=item_id, inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_market_listing_add(self, ctx, listing_id, item_name, price):
        """Логирование добавления предложения на площадку"""
        embed = discord.Embed(
            title="🏪 Предмет выставлен на площадку",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Продавец", value=ctx.author.mention, inline=True)
        embed.add_field(name="Предмет", value=item_name, inline=True)
        embed.add_field(name="Цена", value=f"{price} монет", inline=True)
        embed.add_field(name="ID предложения", value=listing_id, inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_market_purchase(self, ctx, listing_id, item_name, price, seller):
        """Логирование покупки на торговой площадке"""
        embed = discord.Embed(
            title="🏪 Покупка на торговой площадке",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="Покупатель", value=ctx.author.mention, inline=True)
        embed.add_field(name="Продавец", value=seller.mention, inline=True)
        embed.add_field(name="Предмет", value=item_name, inline=True)
        embed.add_field(name="Цена", value=f"{price} монет", inline=True)
        embed.add_field(name="ID предложения", value=listing_id, inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_market_listing_remove(self, ctx, listing_id):
        """Логирование удаления предложения с площадки"""
        embed = discord.Embed(
            title="🏪 Предложение убрано с площадки",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Пользователь", value=ctx.author.mention, inline=True)
        embed.add_field(name="ID предложения", value=listing_id, inline=True)
        await self.send_log(ctx.guild, embed)

    @commands.Cog.listener()
    async def on_inventory_clear(self, ctx, target):
        """Логирование очистки инвентаря"""
        embed = discord.Embed(
            title="🛍️ Инвентарь очищен",
            color=0xff0000,
            timestamp=datetime.now()
        )
        embed.add_field(name="Администратор", value=ctx.author.mention, inline=True)
        embed.add_field(name="Пользователь", value=target.mention, inline=True)
        await self.send_log(ctx.guild, embed)

    # Остальные события логирования (из вашего кода)
    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        if before.name != after.name:
            embed = discord.Embed(
                title="🔄 Изменение названия сервера",
                color=0x3498db,
                timestamp=datetime.now()
            )
            embed.add_field(name="До", value=before.name, inline=True)
            embed.add_field(name="После", value=after.name, inline=True)
            await self.send_log(after, embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot or not message.guild:
            return
            
        embed = discord.Embed(
            title="🗑️ Удалено сообщение",
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        embed.add_field(name="Автор", value=message.author.mention, inline=True)
        embed.add_field(name="Канал", value=message.channel.mention, inline=True)
        
        if len(message.content) > 0:
            content = message.content[:1024] + "..." if len(message.content) > 1024 else message.content
            embed.add_field(name="Содержимое", value=content, inline=False)
        
        await self.send_log(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content or not before.guild:
            return
            
        embed = discord.Embed(
            title="✏️ Изменено сообщение",
            color=0xf39c12,
            timestamp=datetime.now()
        )
        embed.add_field(name="Автор", value=before.author.mention, inline=True)
        embed.add_field(name="Канал", value=before.channel.mention, inline=True)
        
        before_content = before.content[:500] + "..." if len(before.content) > 500 else before.content
        after_content = after.content[:500] + "..." if len(after.content) > 500 else after.content
        
        embed.add_field(name="До", value=before_content or "*пусто*", inline=False)
        embed.add_field(name="После", value=after_content or "*пусто*", inline=False)
        embed.add_field(name="Ссылка", value=f"[Перейти]({after.jump_url})", inline=True)
        
        await self.send_log(before.guild, embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        embed = discord.Embed(
            title="🔨 Пользователь забанен",
            description=f"{user.mention} ({user})",
            color=0xe74c3c,
            timestamp=datetime.now()
        )
        embed.add_field(name="ID", value=user.id, inline=True)
        
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    embed.add_field(name="Модератор", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Причина", value=entry.reason, inline=False)
                    break
        except:
            pass
            
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        embed = discord.Embed(
            title="🔓 Пользователь разбанен",
            description=f"{user.mention} ({user})",
            color=0x00ff00,
            timestamp=datetime.now()
        )
        embed.add_field(name="ID", value=user.id, inline=True)
        
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.unban):
                if entry.target.id == user.id:
                    embed.add_field(name="Модератор", value=entry.user.mention, inline=True)
                    if entry.reason:
                        embed.add_field(name="Причина", value=entry.reason, inline=False)
                    break
        except:
            pass
            
        await self.send_log(guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.guild:
            try:
                async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.kick):
                    if entry.target.id == member.id:
                        embed = discord.Embed(
                            title="👢 Пользователь кикнут",
                            description=f"{member.mention} ({member})",
                            color=0xe67e22,
                            timestamp=datetime.now()
                        )
                        embed.add_field(name="Модератор", value=entry.user.mention, inline=True)
                        if entry.reason:
                            embed.add_field(name="Причина", value=entry.reason, inline=False)
                        await self.send_log(member.guild, embed)
                        break
            except:
                pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel != after.channel and member.guild:
            embed = discord.Embed(
                title="🎤 Изменение голосового статуса",
                color=0x9b59b6,
                timestamp=datetime.now()
            )
            embed.add_field(name="Пользователь", value=member.mention, inline=True)
            
            if not before.channel and after.channel:
                embed.add_field(name="Действие", value="Подключился", inline=True)
                embed.add_field(name="Канал", value=after.channel.name, inline=True)
            elif before.channel and not after.channel:
                embed.add_field(name="Действие", value="Отключился", inline=True)
                embed.add_field(name="Канал", value=before.channel.name, inline=True)
            else:
                embed.add_field(name="Действие", value="Переместился", inline=True)
                embed.add_field(name="Из", value=before.channel.name, inline=True)
                embed.add_field(name="В", value=after.channel.name, inline=True)
            
            await self.send_log(member.guild, embed)

    # Логирование команд бота
    async def log_bot_command(self, ctx, command, target=None, amount=None, reason=None):
        if not ctx.guild:
            return
            
        embed = discord.Embed(
            title="🤖 Команда бота выполнена",
            color=0x7289da,
            timestamp=datetime.now()
        )
        embed.add_field(name="Команда", value=command, inline=True)
        embed.add_field(name="Пользователь", value=ctx.author.mention, inline=True)
        embed.add_field(name="Канал", value=ctx.channel.mention, inline=True)
        
        if target:
            embed.add_field(name="Цель", value=target.mention, inline=True)
        if amount:
            embed.add_field(name="Количество", value=amount, inline=True)
        if reason:
            embed.add_field(name="Причина", value=reason, inline=False)
            
        await self.send_log(ctx.guild, embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))