import asyncio
from telethon import *

import time
import math
import json

initiated = False
clients = []
non_receivers = []
config, login, data = {}, {}, {}

def init(config_file_name, login_file_name, data_file_name):
    global config, login, data, initiated
    config, login, data = read_all(config_file_name, login_file_name, data_file_name)

    print("\nMessageOverImport by \033[1mMatviCoolk\033[0m\nProject \033[1misn't created for any malicious purposes\033[0m\n")
    initiated = True

def read_all(config_file_name, login_file_name, data_file_name):
    data_file = open(data_file_name, "r")
    login_file = open(login_file_name, "r")
    config_file = open(config_file_name, "r")

    data_ = json.loads(data_file.read())
    login_ = json.loads(login_file.read())
    config_ = json.loads(config_file.read())

    data_file.close()
    login_file.close()
    config_file.close()

    return config_, login_, data_

def write_data():
    data_file = open("data.json", "w")
    data_file.write(json.dumps(data, indent=2))
    data_file.close()

def get_time():
    return time.time() // 60

def create_import_file(file_name):
    file = open(file_name, "w")
    file.write('1/1/21, 12:00 am - Messages and calls are end-to-end encrypted. No one outside of this chat,'
               'not even WhatsApp, can read or listen to them. Tap to learn more.\n'
               '1/1/21, 12:00 am - You created group "Group"\n')
    file.close()
    file = open(file_name, "a")
    for i in range(1, 300001):
        file.write(f'1/1/21, 12:00 pm - i: {math.floor(i / 3000)}% - {math.floor(i / 1000)}K\n')
    file.close()

def get_peer(chat_id):
    real_id, peer_type = utils.resolve_id(chat_id)
    return peer_type(real_id)

def tag_events_to_client(self):
    @self.client.on(events.NewMessage(pattern='/id', outgoing=True))
    async def id_command(event):
        real_id, peer_type = utils.resolve_id(event.chat_id)
        await self.client.send_message(event.chat_id,
                                       f"```Full chat ID: {event.chat_id}```\n"
                                       f"```============================```\n"
                                       f"```{peer_type.__name__} : {real_id}```")

    @self.client.on(events.NewMessage(pattern=f'/help'))
    async def help_command(event):
        await self.client.send_message(event.chat_id, "**Command list:**\n\n"
                                                      "/help - send a command list\n"
                                                      "/id - get current chat id\n\n"
                                                      "/import - import to this chat\n"
                                                      "/group - create import group")

    @self.client.on(events.NewMessage(pattern='/group', outgoing=True))
    async def local_create_group_command(event):
        await self.create_group(event)

    @self.client.on(events.NewMessage(pattern='//group'))
    async def global_create_group_command(event):
        await self.create_group(event)

    @self.client.on(events.NewMessage(pattern='/start', outgoing=True))
    async def local_start_command(event):
        await self.start_command(event)

    @self.client.on(events.NewMessage(pattern='//start'))
    async def global_start_command(event):
        await self.start_command(event)

    @self.client.on(events.NewMessage(pattern='/import', outgoing=True))
    async def import_command(event):
        if await self.moi_allowed_chat_check(event): return

        if not self.anything_running:
            await self.full_import(event, event.chat_id)

    @self.client.on(events.NewMessage(pattern="/entity"))
    async def identify_command(event):
        await self.identify()

class Client:
    def __init__(self, num, reciever):
        if not initiated: raise
        self.id = 0
        self.access_hash = 0
        self.input_user = types.InputPeerUser(self.id, self.access_hash)
        self.login = login["clients"][num]
        self.client = self.init_client()
        self.username = ""
        self.num = num

        self.anything_running = False

        if not reciever: non_receivers.append(self)

        self.receiver = reciever

        tag_events_to_client(self)

        self.import_file = None
        self.debug_message = None

        clients.append(self)

    def init_client(self):
        client = TelegramClient(self.login["session"], self.login["app_id"], self.login["app_hash"])
        client.start(self.login["phone"], self.login["password"])
        return client

    async def moi_allowed_chat_check(self, event):
        ret = event.chat_id not in config["moi_allowed_ids"]
        if ret: await self.client.send_message(event.chat_id, 'MOI commands are not allowed in this chat\n')
        return ret

    async def debug_new(self, event, message):
        self.debug_message = await self.client.send_message(event.chat_id, message)
        print(message)

    async def debug(self, event, message):
        self.debug_message = await self.client.edit_message(event.chat_id, self.debug_message, message)
        print(message)

    async def debug_add(self, event, message):
        self.debug_message = await self.client.edit_message(event.chat_id, self.debug_message, self.debug_message.message + " - " + message)
        print(message)

    async def upload_import_file(self):
        self.import_file = await self.client.upload_file("import.txt")
        return self.import_file

    async def check_import(self, event, import_chat_id, checking=True):
        in_use = data["clients"][self.num]["groups"]["in_use"]
        if import_chat_id not in in_use["ids"]:
            await self.client.send_message(event.chat_id, 'Group missing from "data.json"')
            return "next", 0

        index = in_use["ids"].index(import_chat_id)

        if in_use["counts"][index] >= 4:
            if checking:
                await self.client.send_message(event.chat_id, 'This group has already imported the maximum number of times')
            await self.client.send_message(event.chat_id, 'Group deleted')
            data["clients"][self.num]["groups"]["used_ids"].append(in_use["ids"][index])
            in_use["ids"].pop(index)
            in_use["times"].pop(index)
            in_use["counts"].pop(index)
            write_data()
            await self.client.delete_dialog(get_peer(import_chat_id))
            return "next", index

        time_to_wait = min(in_use["times"]) - get_time() + 60 * 24

        if time_to_wait > 0:
            if checking:
                if checking:
                    await self.client.send_message(event.chat_id, f'All groups have already been imported in the last day\n')
                try:
                    await self.create_group(event)
                    await self.client.send_message(event.chat_id, 'Group created')
                    return "next", index
                except Exception as ex:
                    await self.client.send_message(event.chat_id, str(ex))
                    return "new", index

        time_to_wait = round(in_use["times"][index] + 60 * 24 - get_time())

        if in_use["times"][index] > get_time() - 60 * 24:
            if checking:
                await self.client.send_message(event.chat_id, f'This group has already been imported in the last day\n'
                                                              f'Wait {time_to_wait} minutes to import to this group again')
            return "new", index

        time_to_wait = round(max(in_use["times"]) + 70 - get_time())

        if time_to_wait > 0:
            if checking:
                await self.client.send_message(event.chat_id, f'You have already imported in the last 70 minutes\n'
                                                              f'Wait {time_to_wait} minutes to import again')
            return f"wait {time_to_wait}", index

        return "continue", index

    async def full_import(self, event, import_chat_id, checking=True):
        self.anything_running = True

        result, index = await self.check_import(event, import_chat_id, checking)
        if result != "continue":
            return result

        await self.debug_new(event, "Import initiation")
        try:
            init = await self.init_import(import_chat_id)

            await self.debug(event, "Import initiated")
            await self.debug_new(event, "Import start")
            try:
                await self.start_import(init, import_chat_id)
            except Exception as ex:
                await self.debug_add(event, "failed")
                await self.debug_new(event, str(ex))
                return "start failed"
            await self.debug(event, "Import started")
            await self.client.send_message(import_chat_id, 'Import started')
        except Exception as ex:
            await self.debug_add(event, "failed")
            await self.debug_new(event, str(ex))
            return "init failed"

        data["clients"][self.num]["groups"]["in_use"]["counts"][index] += 1
        data["clients"][self.num]["groups"]["in_use"]["times"][index] = get_time()
        write_data()

        self.anything_running = False
        return "succeed"

    async def init_import(self, chat_id):
        return await self.client(functions.messages.InitHistoryImportRequest(
            peer=get_peer(chat_id),
            file=await self.upload_import_file(),
            media_count=0))

    async def start_import(self, init, chat_id):
        return await self.client(functions.messages.StartHistoryImportRequest(
            peer=get_peer(chat_id),
            import_id=init.id))

    async def start_command(self, event):
        if await self.moi_allowed_chat_check(event): return

        if not self.anything_running:
            index = 0
            error_combo = 0
            next_combo = 0
            self.anything_running = True
            while self.anything_running:
                result = await self.full_import(event, data["clients"][self.num]["groups"]["in_use"]["ids"][index], False)
                if result == "next":
                    if next_combo == 0:
                        await self.debug_new(event, result)
                    next_combo += 1
                else:
                    if next_combo > 0:
                        await self.debug_add(event, f"next {next_combo}")
                    next_combo = 0
                    await self.debug_new(event, result)
                if result == "start failed":
                    await asyncio.sleep(10 * 60)
                if result == "succeed":
                    error_combo = 0
                    for i in range(20 * 20):
                        try:
                            await self.client.send_message(data["clients"][self.num]["groups"]["in_use"]["ids"][index], f'Import {round(i / 4)}%')
                        except:
                            pass
                        await asyncio.sleep(3)
                elif result[0:4] == "wait":
                    await asyncio.sleep(int(result[5:]) * 60)
                    index -= 1
                elif result == "init failed" or result == "start failed":
                    await asyncio.sleep(1 * 60)
                    error_combo += 1

                    if error_combo >= 3:
                        await self.client.disconnect()
                        self.init_client()
                elif result == "new":
                    done = False
                    while not done:
                        try:
                            await self.create_group(event)
                            await self.client.send_message(event.chat_id, 'Group created')
                            done = True
                        except errors.FloodWaitError as ex:
                            await asyncio.sleep(ex.seconds + 60 * 60)
                        except:
                            await asyncio.sleep(5 * 60)
                            self.init_client()

                index = (index + 1) % len(data["clients"][self.num]["groups"]["in_use"]["ids"])
                self.anything_running = True

    async def create_group(self, event):
        if await self.moi_allowed_chat_check(event): return

        # group = await self.client(functions.channels.CreateChannelRequest(
        #     f'{self.num} : {str(len(data["clients"][self.num]["groups"]["in_use"]["ids"]) % 1000).zfill(3)}', "",
        #     for_import=True))
        group = await self.client(functions.messages.CreateChatRequest([client.id for client in clients], f'{self.num} : {str(len(data["clients"][self.num]["groups"]["in_use"]["ids"]) % 1000).zfill(3)}'))
        chat_id = group.__dict__["chats"][0].__dict__["id"]
        await self.client(functions.messages.MigrateChatRequest(chat_id))
        real_chat_id = group.__dict__["chats"][0].__dict__["id"]
        #chat_hash = group.__dict__["chats"][0].__dict__["access_hash"]
        await asyncio.sleep(5)

        # await self.debug_new(event, 'Creating link')
        # try:
        #     link = (await self.client(functions.messages.ExportChatInviteRequest(chat_id))).link[14:]
        # except Exception as ex:
        #     await self.debug_add(event, f'{ex}')
        #     return

        # await self.debug_add(event, f'{link}')

        # await self.debug_new(event, f'Adding receivers')
        #
        # for client in clients:
        #     if client.num != self.num and client not in non_receivers:
        #         done = False
        #         while not done:
        #             try:
        #                 await client.client(functions.messages.AddChatUserRequest(real_chat_id, client.input_user, 999
        #                                                                           ))
        #                 await self.debug_add(event, client.num)
        #                 done = True
        #             except Exception as ex:
        #                 print(ex)
        #                 await self.debug_add(event, f'retrying')
        #                 await asyncio.sleep(30)
        if self.num in [client.num for client in non_receivers]:
            try:
                await self.client.edit_folder(chat_id, 1)
            except Exception as ex:
                await self.debug_new(event, f'{ex}')

        # await self.debug_add(event, 'All')

        data["clients"][self.num]["groups"]["in_use"]["ids"].append(chat_id)
        data["clients"][self.num]["groups"]["in_use"]["counts"].append(0)
        data["clients"][self.num]["groups"]["in_use"]["times"].append(0)
        write_data()

        await self.debug_new(event, 'Data written')

    async def identify(self):
        get_me = await self.client.get_me()
        self.username = get_me.username
        self.id = get_me.id
        self.access_hash = get_me.access_hash
        self.input_user = types.InputPeerUser(self.id, self.access_hash)

        #for client in clients:
        #    await self.client.send_message((await client.client.get_me()).username, 'Creating entity')
        #
        #await self.client.edit_folder((await client.client.get_me()).username, 1)

        print("identified")