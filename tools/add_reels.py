#!/usr/bin/env python3
"""
Add four of the client's own walkthrough videos to the On Site reels.

He sent 30 videos in the October pack and none of them were on the site — the
five reels there came from his earlier pack, and they are three bathrooms, a
pantry and a kitchen. These four cover what was missing: a living room, a
study, a wardrobe run and a second kitchen. Clips with a person in frame, the
very short ones and the texture close-ups are left out.

Each is cropped to the 540x720 the existing reels use, muted, trimmed, and
written as MP4 (H.264, faststart) plus WebM (VP9) with a WebP poster.
"""
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
_ROOT = _os.path.dirname(_HERE)          # the site folder
import os, subprocess, json

SRC = ('/tmp/claude-0/-home-claude/2b2f8e9b-d042-5e2c-9c1c-156a9d58eead/scratchpad/'
       'newzip/IBC_Enhanced_Photos_and_Original_Videos/Videos_Original_Unchanged')
OUT = _os.path.join(_ROOT, 'assets/video')
W, H = 540, 720

# (source file, output name, caption, start seconds, length seconds)
CLIPS = [
    # Windows picked off a 1fps filmstrip of each clip. These are hand-held
    # pans and every one of them dwells on a blank cupboard face or a bit of
    # site clutter somewhere; what is kept is the part that shows the room.
    # 20.01.55 and 20.01.56 are the same flat, so they are cut to show
    # different things — the study in one, the media wall in the other.
    ('WhatsApp Video 2026-10-27 at 20.01.56.mp4', 'reel-living-media-wall',
     'Living room · media wall and lit niches', 14, 6),
    ('WhatsApp Video 2026-10-27 at 20.01.55.mp4', 'reel-study-amber-glass',
     'Study desk · amber glass and fluted panelling', 7, 5),
    # this one turns onto plain doors after about 12s, so it stops before that
    ('WhatsApp Video 2026-10-27 at 20.01.49.mp4', 'reel-wardrobe-run',
     'Wardrobe run · amber glazed columns', 7, 5),
    ('WhatsApp Video 2026-10-27 at 20.02.017.mp4', 'reel-kitchen-backsplash',
     'Modular kitchen · stone counter and backsplash', 5, 9),
]

# scale to cover the frame, then crop the centre — same treatment as the
# existing reels, so the row reads as one set
VF = (f'scale={W}:-2:force_original_aspect_ratio=increase,'
      f'crop={W}:{H},setsar=1')


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f'ffmpeg failed:\n{" ".join(cmd[:8])}\n{r.stderr[-600:]}')


for src, name, cap, ss, dur in CLIPS:
    p = os.path.join(SRC, src)
    assert os.path.exists(p), p
    base = ['ffmpeg', '-v', 'error', '-y', '-ss', str(ss), '-t', str(dur), '-i', p]

    run(base + ['-an', '-vf', VF, '-c:v', 'libx264', '-profile:v', 'high',
                '-crf', '27', '-preset', 'slow', '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart', f'{OUT}/{name}.mp4'])
    run(base + ['-an', '-vf', VF, '-c:v', 'libvpx-vp9', '-crf', '36', '-b:v', '0',
                '-row-mt', '1', '-cpu-used', '4', f'{OUT}/{name}.webm'])
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(ss + dur / 2), '-i', p,
         '-frames:v', '1', '-vf', VF, '-q:v', '72', f'{OUT}/{name}-poster.webp'])

    sizes = {e: os.path.getsize(f'{OUT}/{name}.{e}') for e in ('mp4', 'webm')}
    print(f'{name:28s} mp4 {sizes["mp4"]/1024:6.0f} KB   '
          f'webm {sizes["webm"]/1024:6.0f} KB')

json.dump([{'name': n, 'cap': c} for _, n, c, _, _ in CLIPS],
          open(_os.path.join(_HERE, 'new_reels.json'), 'w'), indent=1)
print('\ntotal added:',
      round(sum(os.path.getsize(f'{OUT}/{n}.{e}')
                for _, n, _, _, _ in CLIPS for e in ('mp4', 'webm')) / 1048576, 1), 'MB')
