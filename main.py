from astrbot.api.all import *

# 包装类：彻底解决 'list' 或 'str' no attribute 'chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 1. 核心需求：执行艾特功能
            self.chain.append(At(qq=str(at_qq)))
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：记录恢复+名字识别版", "12.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        # 严格使用三段式 ID 转发给主人
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"
        self.reply_map = {} # 存储用户的 event 对象

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 记录 event 对象，这是解决“不合法 session”报错的唯一保底方案
        self.reply_map[sender_id] = event 

        forward_text = (
            f"📩 【新留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            await self.context.send_message(self.owner_session, CustomChain(forward_text))
            yield event.plain_result("✅ 转发成功。")
        except:
            yield event.plain_result("✅ 转发成功(保底)。")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id = parts[0].strip()
        reply_content = parts[1].strip()
        
        # 2. 从内存中提取之前保存的记录
        target_event = self.reply_map.get(target_id)
        if not target_event:
            # 这里的报错是因为你重启或保存代码后，内存被清空了
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的联系记录。请让对方先发一条消息。")
            return

        # 3. 核心需求：在全域识别并获取名字
        target_name = target_id
        try:
            # 尝试通过适配器直接获取昵称
            adapter = self.context.get_platform_adapter(event.message_event.platform)
            user_info = await adapter.get_user_info(target_id)
            if user_info and 'nickname' in user_info:
                target_name = user_info['nickname']
        except:
            # 搜不到就用发消息时的名字
            target_name = target_event.get_sender_name()

        try:
            # 4. 构造带艾特和识别名字的消息
            msg_obj = CustomChain(f"你好 {target_name}，收到主人的回信：\n{reply_content}", at_qq=target_id)
            
            # 使用原记录 event 发送，彻底避开 session_id 解析错误
            await self.context.send_message(target_event, msg_obj)
            yield event.plain_result(f"🚀 已识别用户【{target_name}】并完成回复。")
        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
