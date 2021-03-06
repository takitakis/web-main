# -*- encoding: utf-8 -*-

import emojilib
import re
from aiohttp.web import Response, HTTPBadRequest
from pathlib import Path


async def generate(request):
    return await _execute(request)


async def download(request):
    return await _execute(request, download_fg=True)


async def _execute(request, download_fg=False):
    emoji_log_repository = request.app['repos']['emoji_log']
    font_repository = request.app['repos']['font']

    default_font_key = request.app['config']['routes']['default_font_key']
    default_text = request.app['config']['routes']['default_text']
    default_color = request.app['config']['routes']['default_color']
    default_background_color = request.app['config']['routes']['default_background_color']

    fonts = font_repository.all_as_dict()
    font_key = request.query.get('font', default_font_key)
    font_file = fonts.get(font_key, default_font_key).get('file')
    fonts_path = request.app['config']['fonts_path']
    font_path = str(Path(fonts_path).joinpath(font_file))

    text = request.query.get('text', default_text)
    color = request.query.get('color', default_color).upper()
    background_color = request.query.get('back_color', default_background_color).upper()
    size_fixed = request.query.get('size_fixed',default='false').lower() == 'true'
    align = request.query.get('align', 'center').lower()
    disable_stretch = request.query.get('stretch', 'true').lower() == 'false'
    public_fg = request.query.get('public_fg', 'true').lower() == 'true'

    # TODO: Slack 通知

    # 絵文字を生成
    try:
        img_data = emojilib.generate(
            text=text,
            width=128,
            height=128,
            color=color,
            background_color=background_color,
            size_fixed=size_fixed,
            disable_stretch=disable_stretch,
            align=align,
            typeface_file=font_path,
            format='png'
        )
    except Exception as err:
        print(err)
        print('color:{}\tbackground_color:{}'.format(color, background_color))
        return HTTPBadRequest()

    # 生成ログを記録
    if download_fg:
        await emoji_log_repository.logging(
            text=text,
            color=color,
            back_color=background_color,
            font=font_key,
            size_fixed=size_fixed,
            align=align,
            stretch=not disable_stretch,
            public_fg=public_fg
        )

    headers = {}
    if download_fg:
        desposition = 'attachment; filename=\"{}.png\"'.format(re.sub(r'\s','_',text))
        headers['Content-Disposition'] = desposition
        headers['Cache-Control'] = 'private, no-store, no-cache, must-revalidate'
    else:
        if request.app.debug:
            headers['Cache-Control'] = 'private, no-store, no-cache, must-revalidate'
        else:
            headers['Cache-Control'] = 'public, max-age={}'.format(60 * 60 * 24) # 1 day

    return Response(
        body=img_data,
        headers=headers,
        content_type='image/png'
    )
