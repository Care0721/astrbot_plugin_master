from astrbot.api.all import *

@register("contact_owner_pro", "Care", "联系主人：终极兼容版", "3.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 1. 这里严格使用你图片里查到的三段式格式
        # 如果是发给你的 QQ 私聊，格式通常是 llbot:FriendMessage:你的QQ
        self.owner_session = "llbot:FriendMessage:3524815759" 
        self.reply_map = {}

    @filter.command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 2. 存下 event 对象，这是回复时绕过 session 校验的唯一生路
        self.reply_map[sender_id] = event

        forward_text = f"📩 【新留言】\n来自：{event.get_sender_name()}({sender_id})\n内容：{msg}\n回复格式：/回复 {sender_id} [内容]"

        try:
            # 3. 放弃所有包装盒，直接发纯文本字符串，这是兼容性最高的
            await self.context.send_message(self.owner_session, forward_text)
            yield event.plain_result("✅ 消息已转发。")
        except Exception as e:
            # 如果三段式私聊也发不出，说明你的 bot 不支持主动私聊，直接在此处报错显示具体原因
            yield event.plain_result(f"❌ 转发失败，原因：{str(e)}")

    @filter.command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 校验权限
        if str(event.get_sender_id()) != "3524815759":
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        try:
            if target_event:
                # 4. 直接把回复塞回原来的 event 路径，这样框架绝对不会报 session 错误
                await self.context.send_message(target_event, f"收到主人的回信：\n\n{reply_text}")
                yield event.plain_result(f"🚀 已成功回复给 {target_id}")
            else:
                yield event.plain_result(f"❌ 找不到该用户的联系记录。")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
