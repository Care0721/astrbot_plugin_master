from astrbot.api.all import *

# 包装类：彻底解决 'list/str object has no attribute chain' 报错
class CustomChain:
    def __init__(self, text, at_qq=None):
        from astrbot.api.message_components import Plain, At
        self.chain = []
        if at_qq:
            self.chain.append(At(qq=str(at_qq))) # 实现艾特
            self.chain.append(Plain(" "))
        self.chain.append(Plain(text))

@register("bot_connector", "Care", "双向沟通：全域识别直连版", "13.0.0")
class BotConnector(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.owner_id = "3524815759" 

    @command("联系主人")
    async def to_owner(self, event: AstrMessageEvent):
        """别人通过此命令联系你"""
        msg = event.message_str.strip()
        if not msg: return
        
        sender_id = str(event.get_sender_id())
        sender_name = event.get_sender_name()
        
        forward_text = f"📩 【新留言】\n来自：{sender_name}({sender_id})\n内容：{msg}\n\n💡 回复指令：\n/回复 {sender_id} 内容"
        
        try:
            # 转发给你，使用格式化的纯数字 ID 避免 session 报错
            await self.context.send_message(self.owner_id, CustomChain(forward_text))
            yield event.plain_result("✅ 消息已传达给主人。")
        except Exception as e:
            yield event.plain_result(f"❌ 转发失败：{str(e)}")

    @command("回复")
    async def to_user(self, event: AstrMessageEvent):
        """你通过此命令主动找任何人"""
        if str(event.get_sender_id()) != self.owner_id: return

        parts = event.message_str.strip().split(maxsplit=1)
        if len(parts) < 2:
            yield event.plain_result("❌ 格式：/回复 [QQ号] [内容]")
            return

        target_qq = parts[0].strip()
        content = parts[1].strip()

        try:
            # 1. 核心：识别名字。尝试从平台所有联系人列表里找人
            target_name = target_qq
            adapter = self.context.get_platform_adapter(event.message_event.platform)
            try:
                # 尝试调用底层 API 获取用户信息（识别昵称）
                info = await adapter.get_user_info(target_qq)
                if info and 'nickname' in info:
                    target_name = info['nickname']
            except:
                pass # 找不到名字就直接用 QQ 号

            # 2. 构造消息体：识别到的名字 + 内容 + 艾特
            response_msg = f"你好 {target_name}，收到主人的回信：\n\n{content}"
            payload = CustomChain(response_msg, at_qq=target_qq)

            # 3. 强制直连发送：直接把 QQ 号传给底层，不经过 session 解析器
            # 这样能绕过 "not enough values to unpack" 的 session 报错
            await self.context.send_message(target_qq, payload)
            
            yield event.plain_result(f"🚀 已识别【{target_name}】并成功私聊投递。")

        except Exception as e:
            # 报错处理
            error_msg = str(e)
            if "expected 3" in error_msg:
                # 如果依然报 session 格式错误，尝试强制拼凑三段式 ID
                try:
                    alt_session = f"llbot:FriendMessage:{target_qq}"
                    await self.context.send_message(alt_session, payload)
                    yield event.plain_result(f"🚀 通过兼容模式成功回复：{target_name}")
                except Exception as e2:
                    yield event.plain_result(f"❌ 依然失败：{str(e2)}")
            else:
                yield event.plain_result(f"❌ 投递失败：{error_msg}")
