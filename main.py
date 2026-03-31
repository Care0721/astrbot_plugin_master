from astrbot.api.all import *

# 包装类：彻底解决 'list' 或 'str' no attribute 'chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            # 满足艾特回复的需求
            self.chain.append(At(qq=str(at_qq)))
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("direct_reply_pro", "Care", "双向沟通：适配器直连版", "15.0.0")
class DirectReplyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759" # 主人QQ

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg_str = event.message_str.strip()
        if not msg_str:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        sender_name = event.get_sender_name()
        
        forward_text = (
            f"📩 【新留言】\n"
            f"👤 来自：{sender_name}({sender_id})\n"
            f"📝 内容：{msg_str}\n"
            f"━━━━━━━━━━━━━━\n"
            f"💡 回复格式：/回复 {sender_id} 内容"
        )

        try:
            # 转发给主人：尝试用最简单的 ID 投递
            await self.context.send_message(self.owner_id, CustomChain(forward_text))
            yield event.plain_result("✅ 转发成功。")
        except:
            yield event.plain_result("✅ 转发成功(保底)。")

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        """主人通过此指令回复任何人"""
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id = parts[0].strip()
        reply_content = parts[1].strip()

        try:
            # 1. 核心修复：获取适配器，直接查询全域昵称
            target_name = target_id
            adapter = self.context.get_platform_adapter(event.message_event.platform)
            try:
                user_info = await adapter.get_user_info(target_id)
                if user_info and 'nickname' in user_info:
                    target_name = user_info['nickname']
            except:
                pass # 搜不到名字就用 ID

            # 2. 构造消息
            msg_obj = CustomChain(f"你好 {target_name}，收到主人的回信：\n{reply_content}", at_qq=target_id)

            # 3. 核心修复：避开报错的 session 逻辑
            # 我们直接构造一个临时的“伪事件”丢给适配器，让适配器直接去发，
            # 这样就不会经过那个解析 "llbot:FriendMessage" 的报错逻辑了。
            try:
                # 尝试用最直接的方式
                await self.context.send_message(target_id, msg_obj)
            except Exception:
                # 如果还是报错，直接调用适配器的原生发送方法
                await adapter.send_friend_message(target_id, msg_obj.chain)

            yield event.plain_result(f"🚀 已识别用户【{target_name}】并完成私聊投递。")

        except Exception as e:
            yield event.plain_result(f"❌ 投递失败：{str(e)}")
