import redis
from shared import ImageDesc
from wand.image import Image
import PIL.Image
import piexif
import time
import cPickle
import os
from datetime import datetime
import io

def main():
    mc = redis.StrictRedis()
    while True:
        hash_value = mc.rpop('_incoming')
        if not hash_value:
            time.sleep(0.25)
            continue
        desc = mc.get(hash_value)
        if not desc:
             continue
        desc = cPickle.loads(desc)
        try:
            desc = desc._replace(status = 'Processing')
            mc.set(hash_value, cPickle.dumps(desc))

            im = Image(filename=os.path.join('upload', hash_value+'.'+desc.ext))
            dt_string = im.metadata.get('exif:DateTimeOriginal')
            uniq = im.metadata.get('exif:UniqueCameraModel')
            mm = im.metadata.get('exif:Make'),im.metadata.get('exif:Model')

            if dt_string is None:
                raise Exception("Image date undefined")

            dt = datetime.strptime(dt_string, '%Y:%m:%d %H:%M:%S')
            if (datetime.now() - dt).days > 365:
                raise Exception("Image too old")

            im.depth = 8
            im.format = 'RGB'
            blob = im.make_blob()
            im = PIL.Image.frombytes('RGB', im.size, blob)
           
            imgif = {}
            model_string = ''
            if uniq:
                model_string = uniq
                imgif[piexif.ImageIFD.UniqueCameraModel] = uniq
            else:
                if mm[0]: 
                    imgif[piexif.ImageIFD.Make] = mm[0]
                if mm[1]: 
                    imgif[piexif.ImageIFD.Model] = mm[1]
                model_string = ' '.join([v for v in mm if v])

            imgif[piexif.ImageIFD.DateTime] = desc.upload_date
            exif = {piexif.ExifIFD.DateTimeOriginal: dt_string,
                piexif.ExifIFD.UserComment: desc.name}
            exif_dict = { "0th": imgif, "Exif":exif }
            exif_bytes = piexif.dump(exif_dict)

            fp = io.BytesIO()  
            im.save(fp, "JPEG", exif = exif_bytes)
            saved = fp.getvalue()  
            size_string = '%i'%len(saved)

            desc = ImageDesc(
                hash_value = hash_value
                , name = desc.name
                , ext = desc.ext
                , upload_date = desc.upload_date
                , creation_date = dt_string
                , camera = model_string
                , size = size_string
                , status = 'OK')
             
            os.remove(os.path.join('upload', hash_value+'.'+desc.ext))
            with open(os.path.join('static', hash_value+'.jpg'), 'wb') as f:
                f.write(saved)
            im.thumbnail((32,32), PIL.Image.ANTIALIAS)
            im.save(os.path.join('static', hash_value+'_thumb.jpg'), "JPEG")
            
            mc.set(hash_value, cPickle.dumps(desc))
            mc.rpush('_images', hash_value) 
        except Exception as e:
            desc = desc._replace(status = str(e))
            mc.setex(hash_value, 60*24, cPickle.dumps(desc))

if __name__ == "__main__":
    main()
