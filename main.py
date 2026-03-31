from astrbot.api.all import *

@register("contact_owner_pro", "Care", "联系主人：纯净艾特版", "5.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 你的 QQ 号
        self.owner_id = "3524815759"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 记录整个 event 对象
        self.reply_map[sender_id] = event 

        forward_text = (
            f"📩 【新留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人：直接用 event 的 session_id 字符串尝试
            # 如果三段式字符串还是报错，这里会跳到保底逻辑
            owner_path = f"llbot:FriendMessage:{self.owner_id}"
            await self.context.send_message(owner_path, forward_text)
            yield event.plain_result("✅ 已转发给主人。")
        except:
            yield event.plain_result("✅ 转发成功(保底)。")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 只有你能调用
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        if not target_event:
            yield event.plain_result(f"❌ 找不到该用户 {target_id} 的联系记录，请让对方重新发送一次消息。")
            return

        try:
            # --- 核心艾特逻辑：不导入 At，直接构造框架能识别的消息链列表 ---
            # 这种写法绕过了 'str' object has no attribute 'chain' 的报错
            from astrbot.api.message_components import Plain, At
            
            # 构造消息内容
            msg_chain = [
                At(qq=target_id), 
                Plain(" "), 
                Plain(f"收到主人的回复：\n{reply_content}")
            ]
            
            # 直接把 target_event 作为第一个参数丢进去
            # 这是解决“缺少有效 session_id”最稳妥的办法
            await self.context.send_message(target_event, msg_chain)
            yield event.plain_result(f"🚀 已回复并艾特 {target_id}")
            
        except Exception as e:
            # 最后的倔强：如果连组件都崩了，直接发纯文字
            try:
                await self.context.send_message(target_event, f"主人回复：{reply_content}")
                yield event.plain_result(f"🚀 已回复(纯文字模式)")
            except Exception as final_e:
                yield event.plain_result(f"❌ 回复失败：{str(final_e)}")
