
import stickybits

TEST_KEY = "c1e1928908a544dbc15b5e0231887a58"

def run_test():
    sb = stickybits.Stickybits(apikey=TEST_KEY)
    sb.base_url = 'http://dev.stickybits.com/api/2/'
    # this barcode image should successfully decode
    print 'bar.jpg', upload_image(sb, 'bar.jpg', codec='Y800')
    # gratuitous use of cyborg kitty
    print 'cyborg_kitty.jpg', upload_image(sb, 'cyborg_kitty.jpg', codec='Y800')
    print ''


def upload_image(sb, code_image, **kwargs):
    data = {}
    headers = None
    data['code_image'] = code_image

    try:
        content_type, body = stickybits.file_encode(data['code_image'])
    except:
        raise stickybits.FileEncodingError

    headers = {
    'Content-Type': content_type
    }
    data = body

    return sb.request('scan.create', kwargs, "POST",
    data=data, headers=headers)


if __name__ == "__main__":
    run_test()