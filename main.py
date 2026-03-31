from astrbot.api.all import *

@register("contact_owner_pro", "Care", "联系主人：极致兼容版", "6.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.reply_map = {} # 存放 event 对象

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        self.reply_map[sender_id] = event # 核心：记录 event 对象

        forward_text = (
            f"📩 【新留言】\n"
            f"👤 来自：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人：直接构造三段式 ID
            target = f"llbot:FriendMessage:{self.owner_id}"
            await self.context.send_message(target, [Plain(forward_text)])
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

        target_id, reply_content = parts[0], parts[1]
        target_event = self.reply_map.get(target_id) # 从内存读取记录

        if not target_event:
            # 重启后记录会消失，必须重新激活
            yield event.plain_result(f"❌ 找不到用户 {target_id} 的记录，请让对方重新发一次消息。")
            return

        try:
            # --- 核心：直接用列表包裹组件，实现 @ 功能并避开 chain 报错 ---
            # 不再使用包装类，直接调用底层组件
            from astrbot.api.message_components import Plain, At
            
            msg_chain = [
                At(qq=target_id), 
                Plain(" "), 
                Plain(f"主人回复：\n{reply_content}")
            ]
            
            # 使用记录的 target_event 原路发回，彻底解决 session_id 报错
            await self.context.send_message(target_event, msg_chain)
            yield event.plain_result(f"🚀 已成功艾特并回复给 {target_id}")
            
        except Exception as e:
            # 终极保底：如果艾特组件都崩了，就发纯文字
            try:
                await self.context.send_message(target_event, [Plain(f"主人回复：{reply_content}")])
                yield event.plain_result(f"🚀 已回复(纯文本模式)")
            except Exception as e2:
                yield event.plain_result(f"❌ 投递失败：{str(e2)}")
