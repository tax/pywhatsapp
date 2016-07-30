import os
import threading
import logging

from yowsup import env
from yowsup.stacks import YowStack, YOWSUP_CORE_LAYERS, YOWSUP_PROTOCOL_LAYERS_FULL
from yowsup.layers import YowLayerEvent
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers.coder import YowCoderLayer
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.interface import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_media.mediauploader import MediaUploader
from yowsup.common import YowConstants
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities import (
    ImageDownloadableMediaMessageProtocolEntity,
    DownloadableMediaMessageProtocolEntity,
    RequestUploadIqProtocolEntity
)

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

EXT_IMAGE = ['.jpg', '.png']
EXT_AUDIO = ['.mp3', '.wav', '.aac', '.wma', '.ogg', '.oga']
EXT_VIDEO = ['.mp4']


class SendLayer(YowInterfaceLayer):
    PROP_MESSAGES = "org.openwhatsapp.yowsup.prop.sendclient.queue"

    def __init__(self):
        super(SendLayer, self).__init__()
        self.ackQueue = []
        self.lock = threading.Condition()

    def get_upload_entity(self, path):
        filename, extension = os.path.splitext(path)
        if extension in EXT_IMAGE:
            return RequestUploadIqProtocolEntity(
                RequestUploadIqProtocolEntity.MEDIA_TYPE_IMAGE, filePath=path
            )
        if extension in EXT_VIDEO:
            return RequestUploadIqProtocolEntity(
                RequestUploadIqProtocolEntity.MEDIA_TYPE_VIDEO, filePath=path
            )
        if extension in EXT_AUDIO:
            return RequestUploadIqProtocolEntity(
                RequestUploadIqProtocolEntity.MEDIA_TYPE_AUDIO, filePath=path
            )
        self.disconnect("ERROR MEDIA")

    @ProtocolEntityCallback("success")
    def on_success(self, success_protocol_entity):
        self.lock.acquire()
        for target in self.getProp(self.__class__.PROP_MESSAGES, []):
            phone, message, is_media = target
            jid = "%s@s.whatsapp.net" % phone
            if is_media:
                path = message
                entity = self.get_upload_entity(path)
                success_fn = lambda success, original: self.on_request_upload_result(jid, path, success, original)
                error_fn = lambda error, original: self.on_request_upload_error(jid, path, error, original)
                self._sendIq(entity, success_fn, error_fn)
            else:
                message_entity = TextMessageProtocolEntity(message, to=jid)
                self.ackQueue.append(message_entity.getId())
                self.toLower(message_entity)
        self.lock.release()

    @ProtocolEntityCallback("ack")
    def on_ack(self, entity):
        self.lock.acquire()
        # if the id match the id in ackQueue, then pop the id of the message out
        if entity.getId() in self.ackQueue:
            self.ackQueue.pop(self.ackQueue.index(entity.getId()))

        if not len(self.ackQueue):
            self.lock.release()
            logger.info("Message sent")
            raise KeyboardInterrupt()

    def disconnect(self, result=None):
        self.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_DISCONNECT))
        if result:
            raise ValueError(result)

    def on_request_upload_result(self, jid, file_path, result_entity, request_entity):
        if result_entity.isDuplicate():
            self.send_file(file_path, result_entity.getUrl(), jid, result_entity.getIp())
        else:
            uploader = MediaUploader(
                jid, self.getOwnJid(),
                file_path,
                result_entity.getUrl(),
                result_entity.getResumeOffset(),
                self.on_upload_success,
                self.on_upload_error,
                self.on_upload_progress,
                async=False
            )
            uploader.start()

    def on_request_upload_error(self, *args):
        self.disconnect("ERROR REQUEST")

    def on_upload_error(self, file_path, jid, url):
        self.disconnect("ERROR UPLOAD")

    def on_upload_success(self, file_path, jid, url):
        self.send_file(file_path, url, jid)

    def on_upload_progress(self, file_path, jid, url, progress):
        logger.info("Progress: {}".format(progress))

    def send_file(self, file_path, url, to, ip=None):
        filename, extension = os.path.splitext(file_path)
        entity = None

        if extension in EXT_IMAGE:
            entity = ImageDownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, ip, to)
        elif extension in EXT_VIDEO:
            entity = DownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, "video", ip, to)
        elif extension in EXT_AUDIO:
            entity = DownloadableMediaMessageProtocolEntity.fromFilePath(file_path, url, "audio", ip, to)
        if entity:
            self.toLower(entity)


class Client(object):

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def _send_message(self, to, message, is_media=False):
        layers = (SendLayer,) + (YOWSUP_PROTOCOL_LAYERS_FULL,) + YOWSUP_CORE_LAYERS
        self.stack = YowStack(layers)
        self.stack.setProp(YowAuthenticationProtocolLayer.PROP_PASSIVE, True)
        self.stack.setProp(YowAuthenticationProtocolLayer.PROP_CREDENTIALS, (self.login, self.password))
        self.stack.setProp(YowNetworkLayer.PROP_ENDPOINT, YowConstants.ENDPOINTS[0])
        self.stack.setProp(YowCoderLayer.PROP_DOMAIN, YowConstants.DOMAIN)
        self.stack.setProp(YowCoderLayer.PROP_RESOURCE, env.YowsupEnv.getCurrent().getResource())

        self.stack.setProp(SendLayer.PROP_MESSAGES, [([to, message, is_media])])
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.stack.loop()
        except KeyboardInterrupt:
            pass

    def send_message(self, to, message):
        self._send_message(to, message)

    def send_media(self, to, path):
        self._send_message(to, path, is_media=True)
