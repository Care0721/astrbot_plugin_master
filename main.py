from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

@register("contact_owner_pro", "YourName", "联系主人Pro：支持双向转发与回复", "1.1.0")
class ContactOwnerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 用于存放最近一次联系主人的用户信息
        # 格式: {"owner_id": {"platform": str, "user_id": str, "user_name": str}}
        self.last_contact = {}

    @filter.command("联系主人")
    async def contact_owner(self, event: AstrMessageEvent):
        '''用户调用：联系机器人主人。用法：/联系主人 [内容]'''
        message_content = event.message_str.strip()
        if not message_content:
            yield event.plain_result("请输入你想对主人说的话。")
            return

        owner_id = self.context.get_config().get("owner_id")
        if not owner_id:
            yield event.plain_result("错误：未配置主人 ID。")
            return

        # 记录来源信息，方便主人回复
        self.last_contact[str(owner_id)] = {
            "platform": event.get_platform_name(),
            "user_id": event.get_sender_id(),
            "user_name": event.get_sender_name()
        }

        forward_text = (
            f"📩 【收到留言】\n"
            f"来自：{event.get_sender_name()} ({event.get_sender_id()})\n"
            f"平台：{event.get_platform_name()}\n"
            f"内容：{message_content}\n"
            f"💡 提示：使用 /回复 [内容] 直接回信。"
        )

        try:
            # 转发给主人
            await self.context.send_message(owner_id, [Plain(forward_text)])
            yield event.plain_result("✅ 消息已送达主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 发送失败：{e}")

    @filter.command("回复")
    async def reply_user(self, event: AstrMessageEvent):
        '''主人调用：回复最后一位留言的用户。用法：/回复 [内容]'''
        owner_id = self.context.get_config().get("owner_id")
        
        # 权限校验：只有主人能使用回复命令
        if str(event.get_sender_id()) != str(owner_id):
            return # 静默处理，非主人不可调用

        reply_content = event.message_str.strip()
        if not reply_content:
            yield event.plain_result("请输入回复内容。")
            return

        # 检查是否有待回复的记录
        target = self.last_contact.get(str(owner_id))
        if not target:
            yield event.plain_result("目前没有待回复的用户记录。")
            return

        try:
            # 构造回传信息
            reply_msg = f"你好，收到主人的回复：\n{reply_content}"
            
            # 发送给原用户
            # 注意：如果跨平台回复，取决于适配器的能力
            await self.context.send_message(target["user_id"], [Plain(reply_msg)])
            
            yield event.plain_result(f"成功回复给 {target['user_name']} ({target['user_id']})")
        except Exception as e:
            yield event.plain_result(f"回复失败：{e}")

