from astrbot.api.all import *
from astrbot.api.event.filter import command 
from astrbot.api.message_components import Plain, At

# 包装盒继续保留，解决属性缺失
class CompatibleMessageChain:
    def __init__(self, components):
        self.chain = components if isinstance(components, list) else [components]

@register("contact_owner_pro", "Care", "联系主人Pro：最终修复版", "2.6.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759"
        self.reply_map = {}

    @command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        msg = event.message_str.strip()
        if not msg:
            yield event.plain_result("请输入内容。")
            return

        sender_id = str(event.get_sender_id())
        # 核心：直接存下 event，后续回复直接用这个对象
        self.reply_map[sender_id] = event

        forward_text = f"📩 【留言】\n来自：{event.get_sender_name()}({sender_id})\n内容：{msg}\n回复格式：/回复 {sender_id} [内容]"

        # 转发给主人：如果私聊地址报错，就直接在当前群艾特你（保证你绝对能收到）
        try:
            # 尝试最标准的私聊 Session 构造方式
            from astrbot.api.provider import Session
            curr_platform = event.message_event.platform # 获取当前平台
            owner_sess = Session(platform=curr_platform, message_type="FriendMessage", session_id=self.owner_id)
            await self.context.send_message(owner_sess, CompatibleMessageChain([Plain(forward_text)]))
            yield event.plain_result("✅ 已转发至主人私聊。")
        except:
            # 如果上面那套复杂的 Session 构造还是不灵，直接群里艾特，这是最后的保底
            yield event.chain_result([At(qq=self.owner_id), Plain(f" 有新留言：\n{forward_text}")])

    @command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        if str(event.get_sender_id()) != self.owner_id:
            return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_id, reply_text = parts[0], parts[1]
        target_event = self.reply_map.get(target_id)

        # 重点修复：直接拿之前的 event 丢进去，这是避开 '缺少有效 session_id' 的终极手段
        if target_event:
            try:
                # 直接传对象，不传字符串地址
                await self.context.send_message(target_event, CompatibleMessageChain([At(qq=target_id), Plain(f" 主人回信：\n{reply_text}")]))
                yield event.plain_result(f"🚀 回复成功")
            except Exception as e:
                # 最后的最后，如果 event 里的 session 过期了，尝试纯字符串强发
                try:
                    await self.context.send_message(target_event.session_id, reply_text)
                    yield event.plain_result(f"🚀 回复成功(文本模式)")
                except:
                    yield event.plain_result(f"❌ 投递失败：{str(e)}")
        else:
            yield event.plain_result(f"❌ 找不到该用户的联系记录。")
