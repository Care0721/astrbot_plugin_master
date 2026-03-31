from astrbot.api.all import *

# 包装类：解决 'str' 或 'list' no attribute 'chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            self.chain.append(At(qq=str(at_qq))) # 需求：艾特目标
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_final", "Care", "联系主人：私聊直连版", "10.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        # 预设主人的三段式 ID
        self.owner_session = f"llbot:FriendMessage:{self.owner_id}"

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        forward_text = (
            f"📩 【新留言】\n"
            f"👤 发送者：{event.get_sender_name()}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} [内容]"
        )

        try:
            # 转发给主人
            await self.context.send_message(self.owner_session, CustomChain(forward_text))
            yield event.plain_result("✅ 消息已转发给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        # 只有主人能用此命令
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id = parts[0].strip()
        reply_content = parts[1].strip()

        # --- 核心改进：直接构造目标私聊的 Session ID ---
        # 强制符合平台要求的 llbot:FriendMessage:ID 格式
        target_session = f"llbot:FriendMessage:{target_id}"

        try:
            # 1. 尝试获取该 QQ 的全域名字 (好友或群友)
            target_name = target_id
            try:
                adapter = self.context.get_platform_adapter(event.message_event.platform)
                user_info = await adapter.get_user_info(target_id)
                if user_info and 'nickname' in user_info:
                    target_name = user_info['nickname']
            except:
                pass

            # 2. 构造带艾特的消息体
            response_text = f"你好 {target_name}，收到主人的私聊回信：\n\n{reply_content}"
            msg_obj = CustomChain(response_text, at_qq=target_id)

            # 3. 直接通过构造的 session_id 发送，不再依赖 reply_map 记录
            await self.context.send_message(target_session, msg_obj)
            yield event.plain_result(f"🚀 已成功识别并私聊回复给：{target_name}({target_id})")
            
        except Exception as e:
            # 如果私聊被拦截(如非好友)，这里会显示报错
            yield event.plain_result(f"❌ 私聊投递失败：{str(e)}\n提示：请确认机器人与对方是好友，或有共同群。")
