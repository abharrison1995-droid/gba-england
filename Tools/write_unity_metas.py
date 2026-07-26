import os
import uuid

base = r"C:\Users\P50\Desktop\Exiled Alvaston\Assets\Art\Placeholders"


def guid():
    return uuid.uuid4().hex


SPRITE_META = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 12
  mipmaps:
    mipMapMode: 0
    enableMipMap: 0
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 0
    aniso: 1
    mipBias: 0
    wrapU: 1
    wrapV: 1
    wrapW: 1
  nPOTScale: 0
  lightmap: 0
  compressionQuality: 50
  spriteMode: 1
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: 32
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 1
  spriteTessellationDetail: -1
  textureType: 8
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings: []
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: {sprite_id}
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
  spritePackingTag: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

TEX_META = """fileFormatVersion: 2
guid: {guid}
TextureImporter:
  internalIDToNameTable: []
  externalObjects: {{}}
  serializedVersion: 12
  mipmaps:
    mipMapMode: 0
    enableMipMap: 1
    sRGBTexture: 1
    linearTexture: 0
    fadeOut: 0
    borderMipMap: 0
    mipMapsPreserveCoverage: 0
    alphaTestReferenceValue: 0.5
    mipMapFadeDistanceStart: 1
    mipMapFadeDistanceEnd: 3
  bumpmap:
    convertToNormalMap: 0
    externalNormalMap: 0
    heightScale: 0.25
    normalMapFilter: 0
    flipGreenChannel: 0
  isReadable: 0
  streamingMipmaps: 0
  streamingMipmapsPriority: 0
  vTOnly: 0
  ignoreMipmapLimit: 0
  grayScaleToAlpha: 0
  generateCubemap: 6
  cubemapConvolution: 0
  seamlessCubemap: 0
  textureFormat: 1
  maxTextureSize: 2048
  textureSettings:
    serializedVersion: 2
    filterMode: 0
    aniso: 1
    mipBias: 0
    wrapU: 0
    wrapV: 0
    wrapW: 0
  nPOTScale: 1
  lightmap: 0
  compressionQuality: 50
  spriteMode: 0
  spriteExtrude: 1
  spriteMeshType: 1
  alignment: 0
  spritePivot: {{x: 0.5, y: 0.5}}
  spritePixelsToUnits: 100
  spriteBorder: {{x: 0, y: 0, z: 0, w: 0}}
  spriteGenerateFallbackPhysicsShape: 1
  alphaUsage: 1
  alphaIsTransparency: 0
  spriteTessellationDetail: -1
  textureType: 0
  textureShape: 1
  singleChannelComponent: 0
  flipbookRows: 1
  flipbookColumns: 1
  maxTextureSizeSet: 0
  compressionQualitySet: 0
  textureFormatSet: 0
  ignorePngGamma: 0
  applyGammaDecoding: 0
  swizzle: 50462976
  cookieLightType: 0
  platformSettings: []
  spriteSheet:
    serializedVersion: 2
    sprites: []
    outline: []
    physicsShape: []
    bones: []
    spriteID: 
    internalID: 0
    vertices: []
    indices: 
    edges: []
    weights: []
  spritePackingTag: 
  pSDRemoveMatte: 0
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

MAT_YAML = """%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: {name}
  m_Shader: {{fileID: 46, guid: 0000000000000000f000000000000000, type: 0}}
  m_Parent: {{fileID: 0}}
  m_ModifiedSerializedProperties: 0
  m_ValidKeywords: []
  m_InvalidKeywords: []
  m_LightmapFlags: 4
  m_EnableInstancingVariants: 0
  m_DoubleSidedGI: 0
  m_CustomRenderQueue: -1
  stringTagMap: {{}}
  disabledShaderPasses: []
  m_LockedProperties: 
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
    - _MainTex:
        m_Texture: {{fileID: 2800000, guid: {tex_guid}, type: 3}}
        m_Scale: {{x: 8, y: 8}}
        m_Offset: {{x: 0, y: 0}}
    m_Ints: []
    m_Floats: []
    m_Colors:
    - _Color: {{r: 1, g: 1, b: 1, a: 1}}
  m_BuildTextureStacks: []
"""

MAT_META = """fileFormatVersion: 2
guid: {guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 2100000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""

tex_guids = {}
for f in os.listdir(base):
    if not f.endswith(".png"):
        continue
    g = guid()
    tex_guids[f] = g
    meta_path = os.path.join(base, f + ".meta")
    if f.startswith("spr_"):
        content = SPRITE_META.format(guid=g, sprite_id=guid())
    else:
        content = TEX_META.format(guid=g)
    with open(meta_path, "w", newline="\n") as fh:
        fh.write(content)
    print("meta", f, g)

pairs = [
    ("mat_grass", "tex_grass.png"),
    ("mat_stone", "tex_stone.png"),
    ("mat_path", "tex_path.png"),
    ("mat_dungeon_floor", "tex_dungeon_floor.png"),
    ("mat_dungeon_wall", "tex_dungeon_wall.png"),
]

mat_guids = {}
for mat_name, tex_name in pairs:
    mg = guid()
    mat_guids[mat_name] = mg
    with open(os.path.join(base, mat_name + ".mat"), "w", newline="\n") as fh:
        fh.write(MAT_YAML.format(name=mat_name, tex_guid=tex_guids[tex_name]))
    with open(os.path.join(base, mat_name + ".mat.meta"), "w", newline="\n") as fh:
        fh.write(MAT_META.format(guid=mg))
    print("mat", mat_name, mg)

# Patch all chunk prefab Ground materials to mat_grass
grass_guid = mat_guids["mat_grass"]
prefab_dir = r"C:\Users\P50\Desktop\Exiled Alvaston\Assets\Prefabs\Chunks"
asphalt_guid = "f5a052633ce0bf44abd169755be20bd5"
for name in os.listdir(prefab_dir):
    if not name.endswith(".prefab"):
        continue
    path = os.path.join(prefab_dir, name)
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if asphalt_guid in text:
        text = text.replace(asphalt_guid, grass_guid)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("patched prefab", name)
    else:
        # also replace any existing material guid on Ground if we can find pattern - skip
        print("no asphalt guid in", name)

print("grass mat guid:", grass_guid)
print("hero sprite guid:", tex_guids.get("spr_hero.png"))
print("bandit sprite guid:", tex_guids.get("spr_bandit.png"))
