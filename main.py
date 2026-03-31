from astrbot.api.all import *

# --- 手动定义兼容层，解决找不到 MessageChain 且必须有 chain 属性的问题 ---
class CompatibleMessageChain:
    def __init__(self, text):
        # 核心：必须给它一个名为 chain 的列表，里面装载 Plain 组件
        from astrbot.api.message_components import Plain
        self.chain = [Plain(text)]

@register("contact_owner_pro", "Care", "联系主人：最终兼容版", "3.2.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 1. 严格使用三段式 ID，解决 expected 3, got 1 报错
        self.owner_session = "llbot:FriendMessage:3524815759" 
        self.reply_map = {}

    # 使用最原始的 command 装饰器，解决 filter 报错问题
    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 2. 存下 event 对象，解决回复时“缺少有效 session_id”的问题
        self.reply_map[sender_id] = event

        forward_text = (
            f"📩 【收到留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 3. 使用手动包装类发送，解决 'str' object has no attribute 'chain'
            chain = CompatibleMessageChain(forward_text)
            await self.context.send_message(self.owner_session, chain)
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 权限校验
        if str(event.get_sender_id()) != "3524815759":
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        try:
            # 同样使用包装类处理回复内容
            reply_chain = CompatibleMessageChain(f"收到主人的回信：\n\n{reply_text}")
            
            if target_event:
                # 4. 顺着 event 对象回传，绕过 session 校验
                await self.context.send_message(target_event, reply_chain)
                yield event.plain_result(f"🚀 已回复给 {target_id}")
            else:
                # 保底回复：拼凑三段式 ID
                target_session = f"llbot:FriendMessage:{target_id}"
                await self.context.send_message(target_session, reply_chain)
                yield event.plain_result(f"🚀 已回复(保底模式)")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
