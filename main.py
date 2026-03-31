from astrbot.api.all import *

# 1. 消息包装类：确保绕过 'list' 或 'str' object has no attribute 'chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            self.chain.append(At(qq=str(at_qq))) # 核心：执行艾特
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：全域识别艾特版", "9.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}" # 严格三段式 ID
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        self.reply_map[sender_id] = event # 记录 event 对象

        forward_text = (
            f"📩 【新留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            await self.context.send_message(self.owner_session, CustomChain(forward_text))
            yield event.plain_result("✅ 留言已成功转发。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        # 尝试通过底层接口获取该 QQ 的昵称 (识别全域联系人)
        target_name = target_id
        try:
            # 这里的逻辑会尝试从机器人缓存或列表中搜索对应 QQ 的名字
            adapter = self.context.get_platform_adapter(event.message_event.platform)
            # 调用底层协议获取用户信息
            user_info = await adapter.get_user_info(target_id)
            if user_info and 'nickname' in user_info:
                target_name = user_info['nickname']
        except:
            # 如果没搜到名字，就用之前的 event 记录里的名字
            if target_event:
                target_name = target_event.get_sender_name()

        if not target_event:
            # 重启后需要重新激活记录
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的联系记录，请让对方先发一条消息。")
            return

        try:
            # 核心：识别名字并在回复中艾特
            final_msg = f"你好 {target_name}，收到主人的回信：\n\n{reply_content}"
            msg_obj = CustomChain(final_msg, at_qq=target_id)
            
            # 原路返回发送，确保 session_id 有效
            await self.context.send_message(target_event, msg_obj)
            yield event.plain_result(f"🚀 已识别用户【{target_name}】并完成艾特回复。")
        except Exception as e:
            yield event.plain_result(f"❌ 回复失败：{str(e)}")
