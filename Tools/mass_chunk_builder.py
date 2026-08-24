#!/usr/bin/env python3
"""
Mass World Chunk Generator for GBH: England (5x5 Britain Region Grid).
Generates:
- Asphalt_Yellowed_Dirt.mat for desolate/wasteland zones
- Prefabs with ground, edge triggers (109.8/110.2), boundary walls (110.0/110.5), NavMeshBaker (1.55m), PlayerSpawnPoint, and road overlays
- MapChunkData assets with bidirectional 4-way orthogonal adjacency wiring
- Updates MapChunkRegistry.asset
"""

import os
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATERIALS_DIR = ROOT / "Assets" / "Materials"
PREFABS_DIR = ROOT / "Assets" / "Prefabs" / "Chunks"
DATA_DIR = ROOT / "Assets" / "Data" / "Chunks"
RESOURCES_DIR = ROOT / "Assets" / "Resources"

# Deterministic GUID generator for consistent re-runs
def make_guid(name: str) -> str:
    # Namespace UUID to 32 hex chars lowercase
    return uuid.uuid5(uuid.NAMESPACE_DNS, f"gbh.england.chunk.{name}").hex

# Built-in Unity References
BUILTIN_PLANE = "{fileID: 10209, guid: 0000000000000000e000000000000000, type: 0}"
BUILTIN_CUBE = "{fileID: 10202, guid: 0000000000000000e000000000000000, type: 0}"
STANDARD_SHADER = "{fileID: 46, guid: 0000000000000000f000000000000000, type: 0}"

# Script GUIDs
GUID_MAP_CHUNK_DATA = "12fb82371264224489fb843eabdf15dd"
GUID_CHUNK_EDGE = "c3449ce0af05e854eb7ccddde7f92355"
GUID_NAVMESH_BAKER = "df2d12075ccf73949b5f4b225e07a889"
GUID_PLAYER_SPAWN = "b8f04285e6c9d454da008ecbb7119bbe"
GUID_REGISTRY = "4b7c1e93a0d5f2c48e6a9b3d17c05fa2"

# Material GUIDs
GUID_MAT_ASPHALT = "f5a052633ce0bf44abd169755be20bd5"
GUID_MAT_GRASS = "c05fd4347e83ce14ba4a0065ed44cf1c"
GUID_MAT_YORKSTONE = "d8f4e129a73c41b89ef7b62a4d38c105"
GUID_MAT_YELLOWED_DIRT = make_guid("material_asphalt_yellowed_dirt")

# Texture GUID for Asphalt
GUID_TEX_ASPHALT = "b587e7fc6cf163c448345021c15bc567"

# Existing chunks with fixed GUIDs
EXISTING_DATA_GUIDS = {
    "Home_London": "5a35b5720ddb68e4ca6ae25fd3467332",
    "East_York": "e819a42f6c8d4732b1154c93a027df91",
}


def build_yellowed_dirt_material():
    mat_file = MATERIALS_DIR / "Asphalt_Yellowed_Dirt.mat"
    meta_file = MATERIALS_DIR / "Asphalt_Yellowed_Dirt.mat.meta"

    mat_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_Name: Asphalt_Yellowed_Dirt
  m_Shader: {STANDARD_SHADER}
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
    - _BumpMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailAlbedoMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailMask:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _DetailNormalMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _EmissionMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _MainTex:
        m_Texture: {{fileID: 2800000, guid: {GUID_TEX_ASPHALT}, type: 3}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _MetallicGlossMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _OcclusionMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    - _ParallaxMap:
        m_Texture: {{fileID: 0}}
        m_Scale: {{x: 1, y: 1}}
        m_Offset: {{x: 0, y: 0}}
    m_Ints: []
    m_Floats:
    - _BumpScale: 1
    - _Cutoff: 0.5
    - _DetailNormalMapScale: 1
    - _DstBlend: 0
    - _GlossMapScale: 1
    - _Glossiness: 0.05
    - _GlossyReflections: 1
    - _Metallic: 0
    - _Mode: 0
    - _OcclusionStrength: 1
    - _Parallax: 0.02
    - _SmoothnessTextureChannel: 0
    - _SpecularHighlights: 1
    - _SrcBlend: 1
    - _UVSec: 0
    - _ZWrite: 1
    m_Colors:
    - _Color: {{r: 0.78, g: 0.7, b: 0.52, a: 1}}
    - _EmissionColor: {{r: 0, g: 0, b: 0, a: 1}}
  m_BuildTextureStacks: []
"""
    meta_content = f"""fileFormatVersion: 2
guid: {GUID_MAT_YELLOWED_DIRT}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 2100000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    with open(mat_file, "w", encoding="utf-8") as f:
        f.write(mat_content)
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(meta_content)
    print(f"Created material: {mat_file.name}")


def generate_chunk_prefab(name: str, ground_mat_guid: str, road_style: str, road_mat_guid: str):
    prefab_file = PREFABS_DIR / f"{name}_Prefab.prefab"
    meta_file = PREFABS_DIR / f"{name}_Prefab.prefab.meta"
    prefab_guid = make_guid(f"prefab_{name}")

    # Build road overlays
    road_children_refs = []
    road_game_objects = []

    if road_style == "NorthSouth":
        road_children_refs.append("- {fileID: 4000008}")
        road_game_objects.append(f"""--- !u!1 &1000008
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000008}}
  - component: {{fileID: 3300008}}
  - component: {{fileID: 2300008}}
  m_Layer: 0
  m_Name: Road_NorthSouth
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000008
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0.04, z: 0}}
  m_LocalScale: {{x: 10, y: 0.04, z: 220}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000005}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300008
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Mesh: {BUILTIN_CUBE}
--- !u!23 &2300008
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Enabled: 1
  m_Materials:
  - {{fileID: 2100000, guid: {road_mat_guid}, type: 2}}
""")
    elif road_style == "EastWest":
        road_children_refs.append("- {fileID: 4000009}")
        road_game_objects.append(f"""--- !u!1 &1000009
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000009}}
  - component: {{fileID: 3300009}}
  - component: {{fileID: 2300009}}
  m_Layer: 0
  m_Name: Road_EastWest
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000009
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0.04, z: 0}}
  m_LocalScale: {{x: 220, y: 0.04, z: 10}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000005}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300009
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  m_Mesh: {BUILTIN_CUBE}
--- !u!23 &2300009
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  m_Enabled: 1
  m_Materials:
  - {{fileID: 2100000, guid: {road_mat_guid}, type: 2}}
""")
    elif road_style == "Crossroad":
        road_children_refs.extend(["- {fileID: 4000008}", "- {fileID: 4000009}"])
        road_game_objects.append(f"""--- !u!1 &1000008
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000008}}
  - component: {{fileID: 3300008}}
  - component: {{fileID: 2300008}}
  m_Layer: 0
  m_Name: Road_NorthSouth
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000008
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0.04, z: 0}}
  m_LocalScale: {{x: 10, y: 0.04, z: 220}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000005}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300008
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Mesh: {BUILTIN_CUBE}
--- !u!23 &2300008
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Enabled: 1
  m_Materials:
  - {{fileID: 2100000, guid: {road_mat_guid}, type: 2}}
--- !u!1 &1000009
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000009}}
  - component: {{fileID: 3300009}}
  - component: {{fileID: 2300009}}
  m_Layer: 0
  m_Name: Road_EastWest
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000009
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0.04, z: 0}}
  m_LocalScale: {{x: 220, y: 0.04, z: 10}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000005}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300009
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  m_Mesh: {BUILTIN_CUBE}
--- !u!23 &2300009
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000009}}
  m_Enabled: 1
  m_Materials:
  - {{fileID: 2100000, guid: {road_mat_guid}, type: 2}}
""")
    elif road_style == "Track":
        road_children_refs.append("- {fileID: 4000008}")
        road_game_objects.append(f"""--- !u!1 &1000008
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000008}}
  - component: {{fileID: 3300008}}
  - component: {{fileID: 2300008}}
  m_Layer: 0
  m_Name: Track_Main
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000008
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0.04, z: 0}}
  m_LocalScale: {{x: 6, y: 0.04, z: 220}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000005}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300008
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Mesh: {BUILTIN_CUBE}
--- !u!23 &2300008
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000008}}
  m_Enabled: 1
  m_Materials:
  - {{fileID: 2100000, guid: {road_mat_guid}, type: 2}}
""")

    paths_children_yaml = "\n  ".join(road_children_refs) if road_children_refs else "[]"
    extra_game_objects_yaml = "\n".join(road_game_objects)

    prefab_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!1 &1000001
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000001}}
  - component: {{fileID: 11400001}}
  m_Layer: 0
  m_Name: {name}_Prefab
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000001
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000001}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {{fileID: 4000002}}
  - {{fileID: 4000003}}
  - {{fileID: 4000004}}
  - {{fileID: 4000010}}
  - {{fileID: 4000011}}
  - {{fileID: 4000012}}
  - {{fileID: 4000013}}
  - {{fileID: 4000014}}
  - {{fileID: 4000015}}
  - {{fileID: 4000016}}
  - {{fileID: 4000017}}
  m_Father: {{fileID: 0}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400001
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000001}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_NAVMESH_BAKER}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  AgentRadius: 0.3
  AgentHeight: 1.55
  AgentClimb: 0.5
  AgentSlope: 45
--- !u!1 &1000002
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000002}}
  - component: {{fileID: 3300002}}
  - component: {{fileID: 2300002}}
  - component: {{fileID: 6400002}}
  m_Layer: 0
  m_Name: Ground
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 12
  m_IsActive: 1
--- !u!4 &4000002
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000002}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 22, y: 1, z: 22}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!33 &3300002
MeshFilter:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000002}}
  m_Mesh: {BUILTIN_PLANE}
--- !u!23 &2300002
MeshRenderer:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000002}}
  m_Enabled: 1
  m_CastShadows: 1
  m_ReceiveShadows: 1
  m_DynamicOccludee: 1
  m_StaticShadowCaster: 0
  m_MotionVectors: 1
  m_LightProbeUsage: 1
  m_ReflectionProbeUsage: 1
  m_RayTracingMode: 2
  m_RayTraceProcedural: 0
  m_RenderingLayerMask: 1
  m_RendererPriority: 0
  m_Materials:
  - {{fileID: 2100000, guid: {ground_mat_guid}, type: 2}}
  m_StaticBatchInfo:
    firstSubMesh: 0
    subMeshCount: 0
  m_StaticBatchRoot: {{fileID: 0}}
  m_ProbeAnchor: {{fileID: 0}}
  m_LightProbeVolumeOverride: {{fileID: 0}}
  m_ScaleInLightmap: 1
  m_ReceiveGI: 1
  m_PreserveUVs: 0
  m_IgnoreNormalsForChartDetection: 0
  m_ImportantGI: 0
  m_StitchLightmapSeams: 1
  m_SelectedEditorRenderState: 3
  m_MinimumChartSize: 4
  m_AutoUVMaxDistance: 0.5
  m_AutoUVMaxAngle: 89
  m_LightmapParameters: {{fileID: 0}}
  m_SortingLayerID: 0
  m_SortingLayer: 0
  m_SortingOrder: 0
  m_AdditionalVertexStreams: {{fileID: 0}}
--- !u!64 &6400002
MeshCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000002}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 5
  m_Convex: 0
  m_CookingOptions: 30
  m_Mesh: {BUILTIN_PLANE}
--- !u!1 &1000003
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000003}}
  - component: {{fileID: 11400003}}
  m_Layer: 0
  m_Name: PlayerSpawn
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000003
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000003}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400003
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000003}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_PLAYER_SPAWN}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  Id: 
--- !u!1 &1000004
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000004}}
  m_Layer: 0
  m_Name: Environment
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000004
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000004}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
  - {{fileID: 4000005}}
  - {{fileID: 4000006}}
  - {{fileID: 4000007}}
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000005
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000005}}
  m_Layer: 0
  m_Name: Paths
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000005
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000005}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children:
  {paths_children_yaml}
  m_Father: {{fileID: 4000004}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000006
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000006}}
  m_Layer: 0
  m_Name: Details
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000006
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000006}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000004}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000007
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000007}}
  m_Layer: 0
  m_Name: Props
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000007
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000007}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 0, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000004}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
{extra_game_objects_yaml}
--- !u!1 &1000010
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000010}}
  - component: {{fileID: 6500010}}
  - component: {{fileID: 11400010}}
  m_Layer: 0
  m_Name: NorthEdge
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000010
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000010}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 1, z: 110.2}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500010
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000010}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 1
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 220, y: 4, z: 0.8}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400010
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000010}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_CHUNK_EDGE}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  EdgeDirection: 0
--- !u!1 &1000011
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000011}}
  - component: {{fileID: 6500011}}
  - component: {{fileID: 11400011}}
  m_Layer: 0
  m_Name: SouthEdge
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000011
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000011}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 1, z: -110.2}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500011
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000011}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 1
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 220, y: 4, z: 0.8}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400011
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000011}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_CHUNK_EDGE}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  EdgeDirection: 1
--- !u!1 &1000012
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000012}}
  - component: {{fileID: 6500012}}
  - component: {{fileID: 11400012}}
  m_Layer: 0
  m_Name: EastEdge
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000012
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000012}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 110.2, y: 1, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500012
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000012}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 1
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 0.8, y: 4, z: 220}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400012
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000012}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_CHUNK_EDGE}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  EdgeDirection: 2
--- !u!1 &1000013
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000013}}
  - component: {{fileID: 6500013}}
  - component: {{fileID: 11400013}}
  m_Layer: 0
  m_Name: WestEdge
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000013
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000013}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: -110.2, y: 1, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500013
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000013}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 1
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 0.8, y: 4, z: 220}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!114 &11400013
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000013}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_CHUNK_EDGE}, type: 3}}
  m_Name: 
  m_EditorClassIdentifier: 
  EdgeDirection: 3
--- !u!1 &1000014
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000014}}
  - component: {{fileID: 6500014}}
  m_Layer: 0
  m_Name: BoundaryWall_North
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000014
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000014}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 2.5, z: 110.5}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500014
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000014}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 230, y: 6, z: 1}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000015
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000015}}
  - component: {{fileID: 6500015}}
  m_Layer: 0
  m_Name: BoundaryWall_South
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000015
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000015}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 0, y: 2.5, z: -110.5}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500015
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000015}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 230, y: 6, z: 1}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000016
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000016}}
  - component: {{fileID: 6500016}}
  m_Layer: 0
  m_Name: BoundaryWall_East
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000016
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000016}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: 110.5, y: 2.5, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500016
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000016}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 1, y: 6, z: 230}}
  m_Center: {{x: 0, y: 0, z: 0}}
--- !u!1 &1000017
GameObject:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  serializedVersion: 6
  m_Component:
  - component: {{fileID: 4000017}}
  - component: {{fileID: 6500017}}
  m_Layer: 0
  m_Name: BoundaryWall_West
  m_TagString: Untagged
  m_Icon: {{fileID: 0}}
  m_NavMeshLayer: 0
  m_StaticEditorFlags: 0
  m_IsActive: 1
--- !u!4 &4000017
Transform:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000017}}
  serializedVersion: 2
  m_LocalRotation: {{x: 0, y: 0, z: 0, w: 1}}
  m_LocalPosition: {{x: -110.5, y: 2.5, z: 0}}
  m_LocalScale: {{x: 1, y: 1, z: 1}}
  m_ConstrainProportionsScale: 0
  m_Children: []
  m_Father: {{fileID: 4000001}}
  m_LocalEulerAnglesHint: {{x: 0, y: 0, z: 0}}
--- !u!65 &6500017
BoxCollider:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 1000017}}
  m_Material: {{fileID: 0}}
  m_IncludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_ExcludeLayers:
    serializedVersion: 2
    m_Bits: 0
  m_LayerOverridePriority: 0
  m_IsTrigger: 0
  m_ProvidesContacts: 0
  m_Enabled: 1
  serializedVersion: 3
  m_Size: {{x: 1, y: 6, z: 230}}
  m_Center: {{x: 0, y: 0, z: 0}}
"""
    meta_content = f"""fileFormatVersion: 2
guid: {prefab_guid}
PrefabImporter:
  externalObjects: {{}}
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    with open(prefab_file, "w", encoding="utf-8") as f:
        f.write(prefab_content)
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(meta_content)
    print(f"Created prefab: {prefab_file.name} (guid: {prefab_guid})")
    return prefab_guid


def generate_map_chunk_data(name: str, coords: tuple, is_city: bool, prefab_guid: str,
                            north_guid: str, south_guid: str, east_guid: str, west_guid: str, data_guid: str = None):
    data_file = DATA_DIR / f"{name}_Data.asset"
    meta_file = DATA_DIR / f"{name}_Data.asset.meta"

    if not data_guid:
        data_guid = make_guid(f"data_{name}")

    def format_ref(guid):
        if not guid:
            return "{fileID: 0}"
        return f"{{fileID: 11400000, guid: {guid}, type: 2}}"

    is_city_val = 1 if is_city else 0

    data_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_MAP_CHUNK_DATA}, type: 3}}
  m_Name: {name}_Data
  m_EditorClassIdentifier: 
  ChunkName: {name}
  Coordinates:
    X: {coords[0]}
    Y: {coords[1]}
  IsCity: {is_city_val}
  IsTutorialDungeon: 0
  LockExitsUntilTutorialComplete: 0
  ChunkPrefab: {{fileID: 1000001, guid: {prefab_guid}, type: 3}}
  NorthChunk: {format_ref(north_guid)}
  SouthChunk: {format_ref(south_guid)}
  EastChunk: {format_ref(east_guid)}
  WestChunk: {format_ref(west_guid)}
  VehicleSpawns: []
  SuppressCheckpointSaves: 0
"""
    meta_content = f"""fileFormatVersion: 2
guid: {data_guid}
NativeFormatImporter:
  externalObjects: {{}}
  mainObjectFileID: 11400000
  userData: 
  assetBundleName: 
  assetBundleVariant: 
"""
    with open(data_file, "w", encoding="utf-8") as f:
        f.write(data_content)
    with open(meta_file, "w", encoding="utf-8") as f:
        f.write(meta_content)
    print(f"Created data asset: {data_file.name} (guid: {data_guid})")
    return data_guid


def main():
    print("=" * 60)
    print("MASS WORLD CHUNK GENERATOR (5x5 Region Grid)")
    print("=" * 60)

    # 1. Build Yellowed Dirt Material
    build_yellowed_dirt_material()

    # 2. Chunk Definitions
    # name, coords, is_city, ground_mat, road_style, road_mat
    CHUNKS_CONFIG = [
        # Center Hub
        {
            "name": "Home_London",
            "coords": (0, 0),
            "is_city": True,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "Crossroad",
            "road_mat": GUID_MAT_ASPHALT,
            "is_existing": True,
            "prefab_guid": "94b71e78235ab1e4284eb2fbaadd87f2",
            "data_guid": EXISTING_DATA_GUIDS["Home_London"],
        },
        # North
        {
            "name": "Hyde_Park_Jungle",
            "coords": (0, 1),
            "is_city": False,
            "ground_mat": GUID_MAT_GRASS,
            "road_style": "Track",
            "road_mat": GUID_MAT_YELLOWED_DIRT,
        },
        # West
        {
            "name": "Barren_Lands_MK",
            "coords": (-1, 0),
            "is_city": False,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "EastWest",
            "road_mat": GUID_MAT_YELLOWED_DIRT,
        },
        # East
        {
            "name": "Commie_Slum_Bolshevik",
            "coords": (1, 0),
            "is_city": False,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "Crossroad",
            "road_mat": GUID_MAT_ASPHALT,
        },
        # South
        {
            "name": "Commie_Slum_Menshevik",
            "coords": (0, -1),
            "is_city": False,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "Crossroad",
            "road_mat": GUID_MAT_ASPHALT,
        },
        # South-West
        {
            "name": "The_Peaks",
            "coords": (-1, -1),
            "is_city": False,
            "ground_mat": GUID_MAT_GRASS,
            "road_style": "Track",
            "road_mat": GUID_MAT_YELLOWED_DIRT,
        },
        # South-East
        {
            "name": "OpenData_Draughtlands",
            "coords": (1, -1),
            "is_city": False,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "NorthSouth",
            "road_mat": GUID_MAT_ASPHALT,
        },
        # Yorkshire Line (Y = -2)
        {
            "name": "East_York",
            "coords": (0, -2),
            "is_city": True,
            "ground_mat": GUID_MAT_YORKSTONE,
            "road_style": "EastWest",
            "road_mat": GUID_MAT_YORKSTONE,
            "is_existing": True,
            "prefab_guid": "a3b8417c8d924151b75294a5c6e8310f",
            "data_guid": EXISTING_DATA_GUIDS["East_York"],
        },
        {
            "name": "Knob_Moor",
            "coords": (-1, -2),
            "is_city": False,
            "ground_mat": GUID_MAT_GRASS,
            "road_style": "EastWest",
            "road_mat": GUID_MAT_YELLOWED_DIRT,
        },
        {
            "name": "West_York",
            "coords": (-2, -2),
            "is_city": True,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "Crossroad",
            "road_mat": GUID_MAT_ASPHALT,
        },
        # Far South-East Coast
        {
            "name": "Brighton",
            "coords": (2, -2),
            "is_city": True,
            "ground_mat": GUID_MAT_ASPHALT,
            "road_style": "Crossroad",
            "road_mat": GUID_MAT_ASPHALT,
        },
    ]

    # Pre-generate or look up GUIDs
    data_guids = {}
    prefab_guids = {}
    coords_to_name = {}

    for c in CHUNKS_CONFIG:
        name = c["name"]
        coords = c["coords"]
        coords_to_name[coords] = name

        if c.get("is_existing"):
            data_guids[name] = c["data_guid"]
            prefab_guids[name] = c["prefab_guid"]
        else:
            data_guids[name] = make_guid(f"data_{name}")
            prefab_guids[name] = make_guid(f"prefab_{name}")

    # Build new prefabs
    for c in CHUNKS_CONFIG:
        if not c.get("is_existing"):
            generate_chunk_prefab(
                name=c["name"],
                ground_mat_guid=c["ground_mat"],
                road_style=c["road_style"],
                road_mat_guid=c["road_mat"],
            )

    # 4-Way Adjacency Resolution:
    # North: (x, y+1)
    # South: (x, y-1)
    # East:  (x+1, y)
    # West:  (x-1, y)
    for c in CHUNKS_CONFIG:
        name = c["name"]
        x, y = c["coords"]

        north_name = coords_to_name.get((x, y + 1))
        south_name = coords_to_name.get((x, y - 1))
        east_name  = coords_to_name.get((x + 1, y))
        west_name  = coords_to_name.get((x - 1, y))

        north_guid = data_guids.get(north_name)
        south_guid = data_guids.get(south_name)
        east_guid  = data_guids.get(east_name)
        west_guid  = data_guids.get(west_name)

        generate_map_chunk_data(
            name=name,
            coords=(x, y),
            is_city=c["is_city"],
            prefab_guid=prefab_guids[name],
            north_guid=north_guid,
            south_guid=south_guid,
            east_guid=east_guid,
            west_guid=west_guid,
            data_guid=data_guids[name],
        )

    # 3. Update MapChunkRegistry.asset
    registry_file = RESOURCES_DIR / "MapChunkRegistry.asset"
    
    # Read existing registry and preserve interiors & special arenas
    all_chunk_assets = list(DATA_DIR.glob("*_Data.asset"))
    registered_guids = []

    # Priority order: Home_London first, then the 5x5 chunks, then all others
    for c in CHUNKS_CONFIG:
        registered_guids.append(data_guids[c["name"]])

    for asset in all_chunk_assets:
        meta_file = asset.with_name(asset.name + ".meta")
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("guid:"):
                        g = line.strip().split()[1]
                        if g not in registered_guids:
                            registered_guids.append(g)
                        break

    chunks_yaml_lines = [f"  - {{fileID: 11400000, guid: {g}, type: 2}}" for g in registered_guids]
    registry_content = f"""%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!114 &11400000
MonoBehaviour:
  m_ObjectHideFlags: 0
  m_CorrespondingSourceObject: {{fileID: 0}}
  m_PrefabInstance: {{fileID: 0}}
  m_PrefabAsset: {{fileID: 0}}
  m_GameObject: {{fileID: 0}}
  m_Enabled: 1
  m_EditorHideFlags: 0
  m_Script: {{fileID: 11500000, guid: {GUID_REGISTRY}, type: 3}}
  m_Name: MapChunkRegistry
  m_EditorClassIdentifier: 
  Chunks:
{chr(10).join(chunks_yaml_lines)}
"""
    with open(registry_file, "w", encoding="utf-8") as f:
        f.write(registry_content)
    print(f"Updated MapChunkRegistry.asset with {len(registered_guids)} chunks.")

    print("=" * 60)
    print("BATCH WORLD CHUNK GENERATION COMPLETE!")
    print("=" * 60)


if __name__ == "__main__":
    main()
