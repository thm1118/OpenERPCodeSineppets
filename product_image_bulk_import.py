# -*- encoding: utf-8 -*-
import os
import xmlrpclib
import base64

"""
根据图片目录中的图片名称，获得对应产品（id或code或自定义SKU），上传图片。
"""

SERVER = 'http://localhost:8069'
DB = ''
USERNAME = ''
USERPASS = ''
#产品图片的根目录地址
IMAGELOCATION = 'd:\\OpenERP'

#登陆取uid
sock_common = xmlrpclib.ServerProxy('%s/xmlrpc/common' % SERVER)
uid = sock_common.login(DB, USERNAME, USERPASS)
sock = xmlrpclib.ServerProxy('%s/xmlrpc/object' % SERVER)


#本函数将数据编码转换成Unicode,目录路径或文件名有中文的,要用此函数重新编码
def u(s, encoding):
    if not s:
        return s
    if isinstance(s, unicode):
        return s
    else:
        return unicode(s, encoding)


def write_to_server(ids, sku, image_file):
    #在openerp里面图片是以二进制来存档，所以要用base64转换，
    image_base64 = base64.encodestring(open(image_file, 'rb').read())
    #print image_base64
    #fixme:需要检查 是否已有图片吗？
    result = sock.execute(DB, uid, USERPASS, 'product.product', 'write', [ids], {'image_medium': image_base64})
    if result:
        imported_images.append(sku)
        print sku+u"--导入图片--"+image_file
    return result

#缓存已导入sku.一个sku目录下可能有多张图片，只导第一张。
imported_images = []

#从图片文件名解析得sku
def get_sku_from_name(image_name):
    #  sY2271732013061816232607870
    if len(image_name) < 8 or image_name[:2] != 'sY':
        return None

    temp_sku = image_name[1:8]

    if temp_sku in imported_images:
        return None
    else:
        return temp_sku

    return None

def get_id_from_sku(image_sku):
    ids = sock.execute(DB, uid, USERPASS, 'product.product', 'search', [('yjh_sku', '=', image_sku)])
    return ids and ids[0]

for root, dirs, files in os.walk(IMAGELOCATION, True, None, False):
    #print root, dir, files
    for f in files:
        if os.path.isfile(os.path.join(root, f)):
            name, ext = os.path.splitext(f)
            #print name, ext
            ext = ext.lower()
            if ext not in ('.jpg', '.png', '.bmp'):
                continue

            sku = get_sku_from_name(name)
            if not sku:
                continue

            image_id = get_id_from_sku(sku)
            if image_id:
                image_file = u(os.path.join(root, f), "gbk")
                write_to_server(image_id, sku, image_file)

print u"--导入图片已完成：'"+str(len(imported_images))+u' 个'

