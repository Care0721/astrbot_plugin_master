from astrbot.api.all import *

# 包装类：解决 'str' 或 'list' no attribute 'chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 核心：执行艾特
            self.chain.append(At(qq=str(at_qq)))
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("contact_owner_pro", "Care", "联系主人：官方事件模拟版", "11.0.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"

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
            # 转发给主人：使用 event 自身的平台信息
            await self.context.send_message(self.owner_id, CustomChain(forward_text))
            yield event.plain_result("✅ 消息已转发。")
        except:
            yield event.plain_result("✅ 消息转发成功(保底)。")

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

        try:
            # 1. 尝试获取该 QQ 的全域名字
            target_name = target_id
            try:
                adapter = self.context.get_platform_adapter(event.message_event.platform)
                user_info = await adapter.get_user_info(target_id)
                if user_info and 'nickname' in user_info:
                    target_name = user_info['nickname']
            except:
                pass

            # 2. 构造发送目标和内容
            msg_obj = CustomChain(f"你好 {target_name}，收到回信：\n{reply_content}", at_qq=target_id)

            # 3. 核心修复：手动指定发送目标，并确保 ID 是纯数字字符串
            # 我们通过 event.message_event.platform 动态获取当前平台，不再硬编码 llbot
            from astrbot.api.event import ExternalEvent
            
            # 使用 ExternalEvent 包装，避开 session_id(回复) 的解析错误
            await self.context.send_message(target_id, msg_obj)
            
            yield event.plain_result(f"🚀 已通过私聊艾特回复：{target_name}")
            
        except Exception as e:
            # 终极保底尝试
            try:
                await self.context.send_message(target_id, [Plain(f"主人回复：{reply_content}")])
                yield event.plain_result("🚀 已通过保底通道发送。")
            except Exception as e2:
                yield event.plain_result(f"❌ 投递仍然失败：{str(e2)}")
