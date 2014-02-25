# -*- encoding: utf-8 -*-
import os
import xmlrpclib
import xlrd
import base64

"""
#从图片名对应产品的excel中，检索OpenERP对应产品，查找对应目录图片，上传。
1、excel格式如下：
image_supplier_id	destination_file_name_id	file_size	desc_zh
V000026	            2008071014203562600.TIF	     26610	    Y000862
V000026	            2008071014203585889.TIF	     20075	    Y000863
V000026	            2008071014203604514.TIF	     25203	    Y000864


2、 注意导出的 sku中会有 Y10000_1,Y10000_2,Y10000_3 这种名称的sku，可能是PI表示多张图片的意思。

3、所有图片都应是jpg。图片名称有TIF的，实际上目录中会有同名 的JPG ，需要改名

4、图片目录中 ，一个图片 会有三份，原始、中等大小，小图片，后两种是通过文件名前缀 b，s 来标识的。导入只需要导入原始，OE会自动做大小

5、导入工具要拷贝到图片所在地，如PI服务器。以通过本地文件路径获取图片。
"""

SERVER = 'http://127.0.0.1:8069'
DB = ''
USERNAME = ''
USERPASS = ''
#产品图片的根目录地址
IMAGELOCATION = 'D:\\OpenERP'
#读取excel文件
#excel表格地址
fname = 'D:\\pi_image_table.xlsx'
bk = xlrd.open_workbook(fname)
#按名字取sheet
sh = bk.sheet_by_index(0)

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

#记录已导入sku.一个sku目录下可能有多张图片，只导第一张。
imported_images = []

def write_to_server(ids, sku, image_file):
    #在openerp里面图片是以二进制来存档，所以要用base64转换，
    image_base64 = base64.encodestring(open(image_file, 'rb').read())
    #print image_base64
    #fixme:需要检查 是否已有图片吗？
    result = sock.execute(DB, uid, USERPASS, 'product.product', 'write', [ids], {'image_medium': image_base64})
    if result:
        imported_images.append(sku)
        print sku+u"--导入图片--"+image_file+u'，已完成：'+str(len(imported_images))+u'个'
    return result

def get_id_from_sku(image_sku):
    ids = sock.execute(DB, uid, USERPASS, 'product.product', 'search', [('yjh_sku', '=', image_sku)])
    return ids and ids[0]


#从本地excel文件循环，再检索远程OE服务，
#速度应该比远程循环拉取所有产品,再在本地excel文件中检索快
for i in range(1, sh.nrows):
    print u"正在处理第"+str(i+1)+u"行/"+str(sh.nrows)
    row_data = sh.row_values(i)
    image_supplier_id = row_data[0]
    destination_file_name_id = row_data[1]
    sku = row_data[3]

    if not (sku and image_supplier_id and destination_file_name_id):
        continue

    if len(sku) > 7:
        sku = sku[:7]

    #只导入遇到的第一张图片
    #todo：当产品支持多图片，需要改进。
    if sku in imported_images:
        continue

    #表里虽然是tif，但实际上还是有对应jpg文件的
    if destination_file_name_id[-3:].lower() not in ('jpg', 'png', 'bmp'):
        destination_file_name_id = destination_file_name_id[:-3]+'jpg'

    image_file = u(os.path.join(IMAGELOCATION, image_supplier_id, destination_file_name_id), "gbk")

    #检查 文件是否存在
    if not os.path.isfile(image_file):
        continue
    #检查库里有没有这个sku
    image_id = get_id_from_sku(sku)
    #库里没有产品则继续
    if not image_id:
        continue

    write_to_server(image_id, sku, image_file)

print u"--导入图片已完成：'"+str(len(imported_images))+u' 个'

