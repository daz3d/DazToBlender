from . import Global
import os
import json


class DtuLoader:
    dtu_dict = dict()
    bone_limits_dict = dict()
    skeleton_data_dict = dict()
    pose_data_dict = dict()
    bone_head_tail_dict = dict()
    morph_links_dict = dict()
    asset_name = ""
    asset_type = ""
    import_name = ""
    materials_list = []

    def load_dtu(self):
        for file in os.listdir(Global.getHomeTown()):
            if file.endswith(".dtu"):
                dtu = os.path.join(Global.getHomeTown(), file)
                break
        with open(dtu, "r") as data:
            self.dtu_dict = json.load(data)

    def get_dtu_dict(self):
        if len(self.dtu_dict.keys()) == 0:
            self.load_dtu()
        return self.dtu_dict

    def load_asset_name(self):
        dtu_dict = self.get_dtu_dict()
        self.asset_name = dtu_dict["Asset Name"]

    def get_asset_name(self):
        if self.asset_name == "":
            self.load_asset_name()
        return self.asset_name

    # DB 2023-Aug-09: asset type
    def load_asset_type(self):
        dtu_dict = self.get_dtu_dict()
        self.asset_type = dtu_dict["Asset Type"]
    
    def get_asset_type(self):
        if self.asset_type == "":
            self.load_asset_type()
        return self.asset_type

    def load_import_name(self):
        dtu_dict = self.get_dtu_dict()
        self.import_name = dtu_dict["Import Name"]

    def get_import_name(self):
        if self.import_name == "":
            self.load_import_name()
        return self.import_name

    def load_bone_head_tail_dict(self):
        dtu_dict = self.get_dtu_dict()
        self.bone_head_tail_dict = dtu_dict["HeadTailData"]

    def get_bone_head_tail_dict(self):
        if len(self.bone_head_tail_dict.keys()) == 0:
            self.load_bone_head_tail_dict()
        return self.bone_head_tail_dict

    def load_bone_limits_dict(self):
        dtu_dict = self.get_dtu_dict()
        self.bone_limits_dict = dtu_dict["LimitData"]

    def get_bone_limits_dict(self):
        if len(self.bone_limits_dict.keys()) == 0:
            self.load_bone_limits_dict()
        return self.bone_limits_dict

    def load_skeleton_data_dict(self):
        dtu_dict = self.get_dtu_dict()
        self.skeleton_data_dict = dtu_dict["SkeletonData"]

    def get_skeleton_data_dict(self):
        if len(self.skeleton_data_dict.keys()) == 0:
            self.load_skeleton_data_dict()
        return self.skeleton_data_dict

    def load_pose_data_dict(self):
        dtu_dict = self.get_dtu_dict()
        data = dtu_dict["PoseData"]
        for key in data:
            if (data[key]["Object Type"] == "MESH") or key.startswith("Genesis"):
                new_key = "root"
                data[key]["Name"] = new_key
                data[key]["Object Type"] = "BONE"
                data[new_key] = data[key]
                del data[key]
                break

        self.pose_data_dict = dtu_dict["PoseData"]

    def get_pose_data_dict(self):
        if len(self.pose_data_dict.keys()) == 0:
            self.load_pose_data_dict()
        return self.pose_data_dict

    def load_materials_list(self):
        dtu_dict = self.get_dtu_dict()
        self.materials_list = dtu_dict["Materials"]

    def get_materials_list(self):
        if len(self.materials_list) == 0:
            self.load_materials_list()
        return self.materials_list

    def load_morph_links_dict(self):
        dtu_dict = self.get_dtu_dict()
        self.morph_links_dict = dtu_dict["MorphLinks"]

    def get_morph_links_dict(self):
        if len(self.morph_links_dict.keys()) == 0:
            self.load_morph_links_dict()
        return self.morph_links_dict


dtu = DtuLoader()

# TODO: Clear out Hardcoded Drivers
class DB:
    def __init__(self):
        pass

    def translate_member_bonenames(self):
        if Global.getIsG9():
            # tbl_basic_bones
            for entry in self.tbl_basic_bones:
                entry[0] = translate_bonenames(entry[0])
    tbl_facems = [
        "EyelidsUpperUp-DownR",
        "MouthCornerUp-DownR",
        "LipTopOut-In",
        "MouthSide-Side",
        "TongueCurl",
        "TongueBendTip",
        "MouthCornerUp-DownL",
        "JawSide-Side",
        "LipTopUp-DownL",
        "MouthWide-NarrowL",
        "EyesSquint-Widen",
        "EyesSquint-WidenL",
        "MouthWide-Narrow",
        "JawOut-In",
        "EyelidsLowerUpDown",
        "BrowOuterUp-DownR",
        "BrowInnerUp-Down",
        "BrowUp-DownL",
        "BrowUp-Down",
        "LipBottomOut-InR",
        "EyelidsUpperUp-Down",
        "MouthCornerForward-Back",
        "BrowOuterUp-Down",
        "BrowInnerUp-DownL",
        "TongueIn-Out",
        "LipsPart",
        "TongueNarrow-Wide",
        "MouthCornerForward-BackR",
        "BrowOuterUp-DownL",
        "LipTopUp-DownR",
        "EyesSideSide",
        "EyesCrossed",
        "EyelidsLowerUpDownR",
        "NostrilsFlex",
        "LipBottomUp-DownR",
        "MouthWide-NarrowR",
        "EyelidsLowerUpDownL",
        "EyesSquint-WidenR",
        "CheekEyeFlexL",
        "CheekFlex-SlackR",
        "LipBottomUp-Down",
        "CheekFlex-SlackL",
        "TongueRaise-Lower",
        "LipBottomOut-InL",
        "MouthCornerUp-Down",
        "LipTopOut-InL",
        "EyesUpDown",
        "LipBottomOut-In",
        "LipTopOut-InR",
        "LipBottomUp-DownL",
        "EyelidsUpperUp-DownL",
        "BrowInnerUp-DownR",
        "TongueSide-Side",
        "BrowUp-DownR",
        "MouthCornerForward-BackL",
        "LipTopUp-Down",
        "CheekFlex-Slack",
        "CheekEyeFlexR",
        "LipsClosed-BareTeeth",
        "TongueUp-Down",
        "CheekEyeFlex",
    ]
    tbl_basic_bones = [
        ["hip", 0],
        ["lThighBend", 0],
        ["lThighTwist", 0],
        ["lShin", 0],
        ["lFoot", 0],
        ["lMetatarsals", 0],
        ["lToe", 0],
        ["lSmallToe4", 0],
        ["lSmallToe4_2", 0],
        ["lSmallToe3", 0],
        ["lSmallToe3_2", 0],
        ["lSmallToe2", 0],
        ["lSmallToe2_2", 0],
        ["lSmallToe1", 0],
        ["lSmallToe1_2", 0],
        ["lBigToe", 0],
        ["lBigToe_2", 0],
        ["rThighBend", 0],
        ["rThighTwist", 0],
        ["rShin", 0],
        ["rFoot", 0],
        ["rMetatarsals", 0],
        ["rToe", 0],
        ["rSmallToe4", 0],
        ["rSmallToe4_2", 0],
        ["rSmallToe3", 0],
        ["rSmallToe3_2", 0],
        ["rSmallToe2", 0],
        ["rSmallToe2_2", 0],
        ["rSmallToe1", 0],
        ["rSmallToe1_2", 0],
        ["rBigToe", 0],
        ["rBigToe_2", 0],
        ["abdomenLower", 0],
        ["abdomenUpper", 0],
        ["chestLower", 0],
        ["chestUpper", 0],
        ["lCollar", 0],
        ["lShldrBend", 0],
        ["lShldrTwist", 0],
        ["lForearmBend", 0],
        ["lForearmTwist", 0],
        ["lHand", 0],
        ["lThumb1", 0],
        ["lThumb2", 0],
        ["lThumb3", 0],
        ["lCarpal1", 0],
        ["lIndex1", 0],
        ["lIndex2", 0],
        ["lIndex3", 0],
        ["lCarpal2", 0],
        ["lMid1", 0],
        ["lMid2", 0],
        ["lMid3", 0],
        ["lCarpal3", 0],
        ["lRing1", 0],
        ["lRing2", 0],
        ["lRing3", 0],
        ["lCarpal4", 0],
        ["lPinky1", 0],
        ["lPinky2", 0],
        ["lPinky3", 0],
        ["rCollar", 0],
        ["rShldrBend", 0],
        ["rShldrTwist", 0],
        ["rForearmBend", 0],
        ["rForearmTwist", 0],
        ["rHand", 0],
        ["rThumb1", 0],
        ["rThumb2", 0],
        ["rThumb3", 0],
        ["rCarpal1", 0],
        ["rIndex1", 0],
        ["rIndex2", 0],
        ["rIndex3", 0],
        ["rCarpal2", 0],
        ["rMid1", 0],
        ["rMid2", 0],
        ["rMid3", 0],
        ["rCarpal3", 0],
        ["rRing1", 0],
        ["rRing2", 0],
        ["rRing3", 0],
        ["rCarpal4", 0],
        ["rPinky1", 0],
        ["rPinky2", 0],
        ["rPinky3", 0],
        ["neckLower", 0],
        ["neckUpper", 0],
        ["head", 0],
        ["upperTeeth", 1],
        ["lowerJaw", 1],
        ["lowerTeeth", 1],
        ["tongue01", 1],
        ["tongue02", 1],
        ["tongue03", 1],
        ["tongue04", 1],
        ["lNasolabialLower", 1],
        ["rNasolabialLower", 1],
        ["lNasolabialMouthCorner", 1],
        ["rNasolabialMouthCorner", 1],
        ["lLipCorner", 1],
        ["lLipLowerOuter", 1],
        ["lLipLowerInner", 1],
        ["LipLowerMiddle", 1],
        ["rLipLowerInner", 1],
        ["rLipLowerOuter", 1],
        ["rLipCorner", 1],
        ["LipBelow", 1],
        ["Chin", 1],
        ["lCheekLower", 1],
        ["rCheekLower", 1],
        ["BelowJaw", 1],
        ["lJawClench", 1],
        ["rJawClench", 1],
        ["rBrowInner", 1],
        ["rBrowMid", 1],
        ["rBrowOuter", 1],
        ["lBrowInner", 1],
        ["lBrowMid", 1],
        ["lBrowOuter", 1],
        ["CenterBrow", 1],
        ["MidNoseBridge", 1],
        ["lEyelidInner", 1],
        ["lEyelidUpperInner", 1],
        ["lEyelidUpper", 1],
        ["lEyelidUpperOuter", 1],
        ["lEyelidOuter", 1],
        ["lEyelidLowerOuter", 1],
        ["lEyelidLower", 1],
        ["lEyelidLowerInner", 1],
        ["rEyelidInner", 1],
        ["rEyelidUpperInner", 1],
        ["rEyelidUpper", 1],
        ["rEyelidUpperOuter", 1],
        ["rEyelidOuter", 1],
        ["rEyelidLowerOuter", 1],
        ["rEyelidLower", 1],
        ["rEyelidLowerInner", 1],
        ["lSquintInner", 1],
        ["lSquintOuter", 1],
        ["rSquintInner", 1],
        ["rSquintOuter", 1],
        ["lCheekUpper", 1],
        ["rCheekUpper", 1],
        ["Nose", 1],
        ["lNostril", 1],
        ["rNostril", 1],
        ["lLipBelowNose", 1],
        ["rLipBelowNose", 1],
        ["lLipNasolabialCrease", 1],
        ["rLipNasolabialCrease", 1],
        ["lNasolabialUpper", 1],
        ["rNasolabialUpper", 1],
        ["lNasolabialMiddle", 1],
        ["rNasolabialMiddle", 1],
        ["LipUpperMiddle", 1],
        ["lLipUpperOuter", 1],
        ["lLipUpperInner", 1],
        ["rLipUpperInner", 1],
        ["rLipUpperOuter", 1],
        ["upperFaceRig", 1],
        ["lEye", 1],
        ["rEye", 1],
        ["lEar", 1],
        ["rEar", 1],
        ["pelvis", 0],
        ["lPectoral", 0],
        ["rPectoral", 0],
        ["lowerFaceRig", 0],
    ]

    tbl_mdrive_g3 = [
        ["pJCMShldrDown_75_L", "lShldrBend", 2, "val*0.764"],
        ["pJCMShldrDown_75_R", "rShldrBend", 2, "val*-0.764"],
        ["pJCMShldrFwd_95_L", "lShldrBend", 0, "val*-0.603"],
        ["pJCMShldrFwd_95_R", "rShldrBend", 0, "val*-0.603"],
        ["pJCMShldrUp_35_L", "lShldrBend", 2, "val*-1.637"],
        ["pJCMShldrUp_35_R", "rShldrBend", 2, "val*1.637"],
        ["pJCMCollarUp_50_L", "lCollar", 2, "val*-1.146"],
        ["pJCMCollarUp_50_R", "rCollar", 2, "val*1.146"],
    ]

    tbl_mdrive = [
        ["pJCMShldrDown_75_L", "lShldrBend", 2, "val*0.764"],
        ["pJCMShldrDown_75_R", "rShldrBend", 2, "val*-0.764"],
        ["pJCMShldrFwd_95_L", "lShldrBend", 0, "val*-0.603"],
        ["pJCMShldrFwd_95_R", "rShldrBend", 0, "val*-0.603"],
        ["pJCMShldrUp_35_L", "lShldrBend", 2, "val*-1.637"],
        ["pJCMShldrUp_35_R", "rShldrBend", 2, "val*1.637"],
        ["pJCMCollarUp_50_L", "lCollar", 2, "val*-1.146"],
        ["pJCMCollarUp_50_R", "rCollar", 2, "val*1.146"],
        ["lShldrBend_CTRLMD_N_YRotate_n110", "lShldrBend", 1, "val*-0.521"],
        ["lShldrBend_CTRLMD_N_ZRotate_90", "lShldrBend", 2, "val*0.637"],
        ["lShldrBend_CTRLMD_N_ZRotate_n40", "lShldrBend", 2, "val*-1.433"],
        ["pJCMAbdomen2Fwd_40", "abdomenUpper", 0, "val*1.433"],
        ["pJCMAbdomen2Side_24_L", "abdomenUpper", 2, "val*-2.389"],
        ["pJCMAbdomen2Side_24_R", "abdomenUpper", 2, "val*2.389"],
        ["pJCMAbdomenFwd_35", "abdomenLower", 0, "val*1.638"],
        ["pJCMAbdomenLowerFwd_Navel", "abdomenLower", 0, "val*1.638"],
        ["pJCMAbdomenUpperFwd_Navel", "abdomenUpper", 0, "val*1.433"],
        ["pJCMBigToeDown_45_L", "lBigToe", 0, "val*1.274"],
        ["pJCMBigToeDown_45_R", "rBigToe", 0, "val*1.274"],
        ["pJCMChestFwd_35", "chestLower", 0, "val*1.638"],
        ["pJCMChestSide_20_L", "chestLower", 2, "val*-2.866"],
        ["pJCMChestSide_20_R", "chestLower", 2, "val*2.866"],
        ["pJCMCollarTwist_n30_L", "lCollar", 1, "val*1.911"],
        ["pJCMCollarTwist_n30_R", "rCollar", 1, "val*-1.911"],
        ["pJCMCollarTwist_p30_L", "lCollar", 1, "val*-1.911"],
        ["pJCMCollarTwist_p30_R", "rCollar", 1, "val*1.911"],
        ["pJCMCollarUp_55_L", "lCollar", 2, "val*-1.042"],
        ["pJCMCollarUp_55_R", "rCollar", 2, "val*1.042"],
        ["pJCMFootDwn_75_L", "lFoot", 0, "val*0.764"],
        ["pJCMFootDwn_75_R", "rFoot", 0, "val*0.764"],
        ["pJCMFootUp_40_L", "lFoot", 0, "val*-1.433"],
        ["pJCMFootUp_40_R", "rFoot", 0, "val*-1.433"],
        ["pJCMForeArmFwd_135_L", "lForearmBend", 0, "(val+1.309)*-0.955"],
        ["pJCMForeArmFwd_135_R", "rForearmBend", 0, "(val+1.309)*-0.955"],
        ["pJCMForeArmFwd_75_L", "lForearmBend", 0, "val*-0.764"],
        ["pJCMForeArmFwd_75_R", "rForearmBend", 0, "val*-0.764"],
        ["pJCMHandDwn_70_L", "lHand", 2, "val*0.819"],
        ["pJCMHandDwn_70_R", "rHand", 2, "val*-0.819"],
        ["pJCMHandUp_80_L", "lHand", 2, "val*-0.717"],
        ["pJCMHandUp_80_R", "rHand", 2, "val*0.717"],
        ["pJCMHeadBack_27", "head", 0, "val*-2.123"],
        ["pJCMHeadFwd_25", "head", 0, "val*2.293"],
        ["pJCMIndex1Dwn_90_L", "lIndex1", 2, "val*0.637"],
        ["pJCMIndex1Dwn_90_R", "rIndex1", 2, "val*-0.637"],
        ["pJCMIndex2Dwn_105_L", "lIndex2", 2, "val*0.546"],
        ["pJCMIndex2Dwn_105_R", "rIndex2", 2, "val*-0.546"],
        ["pJCMIndex3Dwn_90_L", "lIndex3", 2, "val*0.637"],
        ["pJCMIndex3Dwn_90_R", "rIndex3", 2, "val*-0.637"],
        ["pJCMMid1Dwn_95_L", "lMid1", 2, "val*0.603"],
        ["pJCMMid1Dwn_95_R", "rMid1", 2, "val*-0.603"],
        ["pJCMMid2Dwn_105_L", "lMid2", 2, "val*0.546"],
        ["pJCMMid2Dwn_105_R", "rMid2", 2, "val*-0.546"],
        ["pJCMMid3Dwn_90_L", "lMid3", 2, "val*0.637"],
        ["pJCMMid3Dwn_90_R", "rMid3", 2, "val*-0.637"],
        ["pJCMNeckBack_27", "neckUpper", 0, "val*-0.7581"],
        ["pJCMNeckBack_27", "neckLower", 0, "val2*-1.197"],
        ["pJCMNeckFwd_35", "neckUpper", 0, "val*0.76203"],
        ["pJCMNeckFwd_35", "neckLower", 0, "val2*1.20327"],
        ["pJCMNeckLowerSide_40_L", "neckLower", 2, "val*-1.911"],
        ["pJCMNeckLowerSide_40_R", "neckLower", 2, "val*1.911"],
        ["pJCMNeckTwist_22_L", "neckLower", 1, "val*2.606"],
        ["pJCMNeckTwist_22_R", "neckLower", 1, "val*-2.606"],
        ["pJCMNeckTwist_Reverse", "neckLower", 0, "val*1.433"],
        ["pJCMPelvisFwd_25", "pelvis", 0, "val*2.293"],
        ["pJCMPinky1Dwn_95_L", "lPinky1", 2, "val*0.637"],
        ["pJCMPinky1Dwn_95_R", "rPinky1", 2, "val*-0.637"],
        ["pJCMPinky2Dwn_105_L", "lPinky2", 2, "val*0.546"],
        ["pJCMPinky2Dwn_105_R", "rPinky2", 2, "val*-0.546"],
        ["pJCMPinky3Dwn_90_L", "lPinky3", 2, "val*0.637"],
        ["pJCMPinky3Dwn_90_R", "rPinky3", 2, "val*-0.637"],
        ["pJCMRing1Dwn_95_L", "lRing1", 2, "val*0.637"],
        ["pJCMRing1Dwn_95_R", "rRing1", 2, "val*-0.637"],
        ["pJCMRing2Dwn_105_L", "lRing2", 2, "val*0.546"],
        ["pJCMRing2Dwn_105_R", "rRing2", 2, "val*-0.546"],
        ["pJCMRing3Dwn_90_L", "lRing3", 2, "val*0.637"],
        ["pJCMRing3Dwn_90_R", "rRing3", 2, "val*-0.637"],
        ["pJCMShinBend_155_L", "lShin", 0, "(val-1.571)*0.882"],
        ["pJCMShinBend_155_R", "rShin", 0, "(val-1.571)*0.882"],
        ["pJCMShinBend_90_L", "lShin", 0, "val*0.637"],
        ["pJCMShinBend_90_R", "rShin", 0, "val*0.637"],
        ["pJCMShldrDown_40_L", "lShldrBend", 2, "val*1.433"],
        ["pJCMShldrDown_40_R", "rShldrBend", 2, "val*-1.433"],
        ["pJCMShldrFwd_110_L", "lShldrBend", 0, "val*-0.521"],
        ["pJCMShldrFwd_110_R", "rShldrBend", 0, "val*-0.521"],
        ["pJCMShldrUp_90_L", "lShldrBend", 2, "val*-0.637"],
        ["pJCMShldrUp_90_R", "rShldrBend", 2, "val*0.637"],
        ["pJCMThighBack_35_L", "lThighBend", 0, "val*1.638"],
        ["pJCMThighBack_35_R", "rThighBend", 0, "val*1.638"],
        ["pJCMThighFwd_115_L", "lThighBend", 0, "(val+0.995)*-0.988"],
        ["pJCMThighFwd_115_R", "rThighBend", 0, "(val+0.995)*-0.988"],
        ["pJCMThighFwd_57_L", "lThighBend", 0, "val*-1.006"],
        ["pJCMThighFwd_57_R", "rThighBend", 0, "val*-1.006"],
        ["pJCMThighSide_85_L", "lThighBend", 2, "val*-0.674"],
        ["pJCMThighSide_85_R", "rThighBend", 2, "val*0.674"],
        ["pJCMThumb1Bend_50_L", "lThumb1", 0, "val*1.146"],
        ["pJCMThumb1Bend_50_R", "rThumb1", 0, "val*1.146"],
        ["pJCMThumb1Up_20_L", "lThumb1", 2, "val*-2.866"],
        ["pJCMThumb1Up_20_R", "rThumb1", 2, "val*2.866"],
        ["pJCMThumb2Bend_65_L", "lThumb2", 0, "val*0.882"],
        ["pJCMThumb2Bend_65_R", "rThumb2", 0, "val*0.882"],
        ["pJCMThumb3Bend_90_L", "lThumb3", 0, "val*0.637"],
        ["pJCMThumb3Bend_90_R", "rThumb3", 0, "val*0.637"],
        ["pJCMToesUp_60_L", "lToe", 0, "val*-0.955"],
        ["pJCMToesUp_60_R", "rToe", 0, "val*-0.955"],
        ["rShldrBend_CTRLMD_N_YRotate_110", "rShldrBend", 1, "val*0.521"],
        ["rShldrBend_CTRLMD_N_ZRotate_40", "rShldrBend", 2, "val*1.433"],
        ["rShldrBend_CTRLMD_N_ZRotate_n90", "rShldrBend", 2, "val*-0.637"],
        #  ['EyesSideSide', 'sight', 2, 'val * -0.955'],
        #  ['EyesSideR', 'sight', 2, 'val * -0.955'],
        #  ['EyesSideL', 'sight', 2, 'val * 0.955'],
        #  ['EyesUpDown', 'sight', 0, 'val * 0.955'],
    ]

    def kind9(self, arg, lr):
        bones = ["thigh", "shin", "upper_arm", "forearm"]
        ans = [
            "ORG-",
            "",
            "_fk",
            "_ik",
            "_parent",
            "DEF-",
            "DEF-",
            "MCH-._ik",
            "MCH-._ik_stretch.",
        ]  # 6->.001 11, 12
        for i in range(len(ans)):
            if i == 0 or i == 5 or i == 6:
                ans[i] = ans[i] + arg
            elif i < 5:
                ans[i] = arg + ans[i]
            elif i == 7 or i == 8:
                ans[i] = "MCH-" + arg + "_ik"
                if i == 8:
                    ans[i] += "_stretch"
            ans[i] += "." + lr
            if i == 6:
                ans[i] += ".001"
        return ans

    def mix_range(self, arg):
        ans = [0, 0, 0, 0, 0, 0]
        bone_limits = dtu.get_bone_limits_dict()
        for bone_limit_key in bone_limits:
            bone_limit = bone_limits[bone_limit_key]
            if bone_limit[0].startswith(arg):
                for i in range(6):
                    v = bone_limit[i + 2]
                    if v != 0:
                        ans[i] = bone_limit[i + 2]
        return ans

    tbl_blimit_rgfy = [
        ["chest", [-50, 50, -40, 40, -45, 45]],
        ["hips", [-50, 35, -35, 35, -30, 30]],
        ["neck", [-42, 35, -45, 45, -30, 30]],
        ["tweak_spine", [-50, 40, -20, 20, -15, 15]],
    ]

    toRigify = [
        [8, "lForearmBend", "forearm.L"],
        [8, "lForearmTwist", "forearm.L.001"],
        [8, "lThighBend", "thigh.L"],
        [8, "lThighTwist", "thigh.L.001"],
        [8, "lShldrBend", "upper_arm.L"],
        [8, "lShldrTwist", "upper_arm.L.001"],
        [7, "lShin", "shin.L"],
        [6, "lShin", "shin.L.001"],
        [1, "lShin", "shin.L"],
        [0, "lShin", "shin.L"],
        [1, "lThighBend", "thigh.L"],
        [0, "lThighTwist", "thigh.L"],
        [2, "lMetatarsals", "foot.L"],
        [4, "lFoot", "foot.L"],
        [2, "lToe", "toe.L"],
        [2, "pelvis", "pelvis.L"],
        [2, "pelvis", "pelvis.R"],
        [2, "abdomenLower", "spine"],
        [2, "abdomenUpper", "spine.001"],
        [2, "chestLower", "spine.002"],
        [2, "chestUpper", "spine.003"],
        [2, "neckLower", "spine.004"],
        [2, "neckUpper", "spine.005"],
        [2, "head", "spine.006"],
        [2, "head", "face"],
        [2, "lCollar", "shoulder.L"],
        [1, "lShldrBend", "upper_arm.L"],
        [0, "lShldrTwist", "upper_arm.L"],
        [1, "lForearmBend", "forearm.L"],
        [0, "lForearmTwist", "forearm.L"],
        [3, "lHand", "hand.L"],
        [2, "lCarpal4", "palm.04.L"],
        [2, "lCarpal3", "palm.03.L"],
        [2, "lCarpal2", "palm.02.L"],
        [2, "lCarpal1", "palm.01.L"],
        [2, "lPinky1", "f_pinky.01.L"],
        [2, "lRing1", "f_ring.01.L"],
        [2, "lMid1", "f_middle.01.L"],
        [2, "lIndex1", "f_index.01.L"],
        [2, "lPinky2", "f_pinky.02.L"],
        [2, "lRing2", "f_ring.02.L"],
        [2, "lMid2", "f_middle.02.L"],
        [2, "lIndex2", "f_index.02.L"],
        [2, "lPinky3", "f_pinky.03.L"],
        [2, "lRing3", "f_ring.03.L"],
        [2, "lMid3", "f_middle.03.L"],
        [2, "lIndex3", "f_index.03.L"],
        [2, "lThumb1", "thumb.01.L"],
        [2, "lThumb2", "thumb.02.L"],
        [2, "lThumb3", "thumb.03.L"],
        [2, "lPectoral", "breast.L"],
    ]

    tometaface_couple = [
        [0, "brow.T.L", "forehead.L.002"],
        [0, "brow.T.L.001", "forehead.L.001"],
        [0, "brow.T.L.002", "forehead.L"],
        [
            1,
            "brow.T.L",
            "cheek.T.L",
        ],
        [5, "ear.L", "ear.L.004"],
        [9, "nose.L", "nose.L.001"],
        [5, "cheek.B.L", "lip.T.L.001"],
        [5, "cheek.B.L", "lip.B.L.001"],  # head to tail = 9
        [9, "cheek.B.L.001", "cheek.T.L"],
        [0, "nose.001", "nose.L.001"],
        [5, "nose", "brow.T.L.003"],  # tail to head = 5
    ]

    tometaface_f = [
        [1, "heel.02.L", 910],
        [0, "heel.02.L", 311],
        [0, "chin.L", 6527],
        [1, "cheek.B.L", 6527],
        [
            1,
            "eye.L",
            15888,
            15889,
            15891,
            15895,
            15897,
            15898,
            15899,
            15900,
            15914,
            15915,
            15917,
            15921,
            15923,
            15924,
            15925,
            15926,
            15938,
            15939,
            15946,
            15948,
            15952,
            15954,
            15955,
            15956,
            15965,
            15967,
            15971,
            15973,
            15974,
            15975,
            15984,
            15985,
        ],
        [
            0,
            "eye.L",
            15944,
        ],
        [
            1,
            "jaw",
            11,
            1696,
            8206,
        ],
        [
            1,
            "chin",
            6453,
            6458,
            12837,
        ],
        [
            1,
            "chin.001",
            38,
            64,
        ],
        [
            0,
            "chin.001",
            61,
        ],
        [
            1,
            "lip.B.L",
            6526,
        ],
        [
            1,
            "lip.B.L.001",
            6512,
        ],
        [
            1,
            "lip.T.L",
            19,
            6524,
        ],
        [
            1,
            "lip.T.L.001",
            6516,
        ],
        [
            0,
            "",
            727,
            728,
            729,
        ],
        [
            1,
            "chin.L",
            1664,
        ],
        [
            1,
            "jaw.L.001",
            1665,
            2518,
        ],
        [
            1,
            "jaw.L",
            1668,
            1671,
            5318,
        ],
        [
            1,
            "temple.L",
            701,
            4817,
            4818,
        ],
        [
            1,
            "cheek.B.L.001",
            4795,
            4798,
        ],
        [
            1,
            "forehead.L",
            2621,
            4806,
            4807,
        ],
        [
            1,
            "forehead.L.001",
            2615,
            2616,
        ],
        [
            1,
            "forehead.L.002",
            2610,
            5336,
            5337,
        ],
        [
            0,
            "nose.004",
            5255,
        ],
        [
            1,
            "nose.004",
            2431,
            8941,
        ],
        [
            1,
            "nose.003",
            2428,
            8938,
        ],
        [
            1,
            "nose.002",
            60,
        ],
        [
            1,
            "nose.001",
            63,
            65,
        ],
        [
            1,
            "nose",
            5231,
            11700,
        ],
        [
            1,
            "brow.T.L.003",
            2374,
        ],
        [
            1,
            "brow.T.L.002",
            776,
            2319,
            2584,
        ],
        [
            1,
            "brow.T.L.001",
            2585,
        ],
        [
            1,
            "brow.T.L",
            2513,
        ],
        [
            1,
            "nose.L.001",
            3916,
            3917,
        ],
        [
            1,
            "nose.L",
            2408,
            5308,
        ],
        [
            1,
            "cheek.T.L.001",
            2458,
            5306,
        ],
        [
            0,
            "brow.B.L.003",
            6375,
        ],
        [
            1,
            "brow.B.L.003",
            6386,
        ],
        [
            1,
            "brow.B.L.002",
            6394,
        ],
        [
            1,
            "brow.B.L.001",
            6391,
        ],
        [
            1,
            "brow.B.L",
            2504,
        ],
        [
            1,
            "eyelid.B.L",
            1682,
            1692,
        ],
        [
            1,
            "eyelid.B.L.001",
            675,
            678,
        ],
        [
            1,
            "eyelid.B.L.002",
            989,
            994,
        ],
        [
            1,
            "eyelid.B.L.003",
            672,
            681,
        ],
        [
            1,
            "eyelid.T.L",
            2336,
        ],
        [
            1,
            "eyelid.T.L.001",
            610,
        ],
        [
            1,
            "eyelid.T.L.002",
            616,
            619,
        ],
        [
            1,
            "eyelid.T.L.003",
            789,
        ],
        [
            1,
            "ear.L.004",
            5615,
            5616,
            6497,
        ],
        [
            1,
            "ear.L",
            2138,
            6585,
        ],
        [
            1,
            "ear.L.001",
            5609,
            6582,
        ],
        [
            1,
            "ear.L.002",
            5607,
            6467,
        ],
        [
            1,
            "ear.L.003",
            5605,
            6462,
            6487,
            6489,
        ],
        [
            1,
            "teeth.T",
            5831,
        ],
        [
            1,
            "teeth.B",
            5940,
        ],
        [
            0,
            "teeth.T",
            5852,
            12280,
        ],
        [
            0,
            "teeth.B",
            5917,
            12345,
        ],
        [
            1,
            "tongue",
            5732,
            5733,
        ],
        [
            1,
            "tongue.001",
            6158,
            12551,
        ],
        [
            1,
            "tongue.002",
            5722,
            12168,
        ],
        [
            0,
            "tongue.002",
            6400,
            12787,
        ],
        [0, "lid.T.L.003", 1692],
        [0, "lid.B.L", 2353],
        [0, "lid,B.L.001", 2359],
        [1, "lid.B.L.002", 2359],
        [0, "lid.B.L.002", 2356],
        [0, "lid.B.L.003", 2362],
        [1, "lid.T.L", 2362],
        [0, "lid.T.L", 2345],
        [0, "lid.T.L.001", 2342],
        [0, "lid.T.L.002", 2348],
    ]

    tometaface_m = [
        [1, "heel.02.L", 858],
        [0, "heel.02.L", 291],
        [0, "chin.L", 6199],
        [1, "cheek.B.L", 6199],
        [
            0,
            "eye.L",
            15772,
        ],
        [
            1,
            "eye.L",
            15716,
            15717,
            15719,
            15723,
            15725,
            15726,
            15727,
            15728,
            15742,
            15743,
            15745,
            15749,
            15751,
            15752,
            15753,
            15754,
            15766,
            15767,
            15774,
            15776,
            15780,
            15782,
            15783,
            15784,
            15793,
            15795,
            15799,
            15801,
            15802,
            15803,
            15812,
            15813,
        ],
        [
            1,
            "jaw",
            11,
        ],
        [
            1,
            "chin",
            6125,
            6130,
            12187,
        ],
        [
            1,
            "chin.001",
            36,
            64,
            2191,
            2239,
            8377,
            8425,
        ],
        [
            0,
            "chin.001",
            62,
        ],
        [
            1,
            "lip.B.L",
            6198,
        ],
        [
            1,
            "lip.B.L.001",
            6184,
        ],
        [
            1,
            "lip.T.L",
            19,
            6196,
        ],
        [
            1,
            "lip.T.L.001",
            6188,
        ],
        [
            0,
            "",
            707,
            708,
            709,
        ],
        [
            1,
            "chin.L",
            1560,
        ],
        [
            1,
            "jaw.L.001",
            1561,
            2342,
            2369,
        ],
        [
            1,
            "jaw.L",
            1564,
            1567,
            5014,
        ],
        [
            1,
            "temple.L",
            681,
            4537,
            4538,
        ],
        [
            1,
            "cheek.B.L.001",
            4515,
            4518,
        ],
        [
            1,
            "forehead.L",
            2448,
            4526,
            4527,
        ],
        [
            1,
            "forehead.L.001",
            2442,
            2443,
        ],
        [
            1,
            "forehead.L.002",
            2437,
            5032,
        ],
        [
            0,
            "nose.004",
            4951,
        ],
        [
            1,
            "nose.004",
            2282,
            8468,
        ],
        [
            1,
            "nose.003",
            9,
            66,
        ],
        [
            1,
            "nose.002",
            42,
            60,
        ],
        [
            1,
            "nose.001",
            2245,
            8431,
        ],
        [
            1,
            "nose",
            4927,
            11074,
        ],
        [
            1,
            "brow.T.L.003",
            2225,
        ],
        [
            1,
            "brow.T.L.002",
            756,
            2170,
            2411,
        ],
        [
            1,
            "brow.T.L.001",
            2412,
        ],
        [
            1,
            "brow.T.L",
            2364,
            2366,
        ],
        [
            1,
            "nose.L.001",
            2233,
            2235,
            3721,
        ],
        [
            1,
            "nose.L",
            2264,
        ],
        [
            1,
            "cheek.T.L.001",
            5000,
            5002,
        ],
        [
            0,
            "brow.B.L.003",
            6071,
        ],
        [
            1,
            "brow.B.L.003",
            2350,
            6082,
        ],
        [
            1,
            "brow.B.L.002",
            2353,
            6090,
        ],
        [
            1,
            "brow.B.L.001",
            2358,
            6086,
            6087,
        ],
        [
            1,
            "brow.B.L",
            2355,
        ],
        [
            1,
            "eyelid.B.L",
            1577,
            1587,
        ],
        [
            1,
            "eyelid.B.L.001",
            655,
            658,
        ],
        [
            1,
            "eyelid.B.L.002",
            936,
            941,
        ],
        [
            1,
            "eyelid.B.L.003",
            652,
            661,
        ],
        [
            1,
            "eyelid.T.L",
            2218,
            2219,
        ],
        [
            1,
            "eyelid.T.L.001",
            590,
        ],
        [
            1,
            "eyelid.T.L.002",
            596,
            599,
        ],
        [
            1,
            "eyelid.T.L.003",
            766,
            769,
        ],
        [
            1,
            "ear.L.004",
            5311,
            5312,
            6169,
        ],
        [
            1,
            "ear.L",
            1998,
            2005,
            2008,
            6252,
        ],
        [
            1,
            "ear.L.001",
            5305,
            6249,
        ],
        [
            1,
            "ear.L.002",
            5303,
            6139,
        ],
        [
            1,
            "ear.L.003",
            5301,
            6134,
            6159,
            6161,
        ],
        [
            1,
            "teeth.T",
            5527,
        ],
        [
            1,
            "teeth.B",
            5636,
        ],
        [
            0,
            "teeth.T",
            5548,
            11654,
        ],
        [
            0,
            "teeth.B",
            5613,
            11719,
        ],
        [
            1,
            "tongue",
            5428,
            5429,
        ],
        [
            1,
            "tongue.001",
            5854,
            11925,
        ],
        [
            1,
            "tongue.002",
            5418,
            11542,
        ],
        [
            0,
            "tongue.002",
            6093,
            6096,
            12159,
            12161,
        ],
        [0, "lid.T.L.003", 2211],
        [0, "lid.B.L", 2204],
        [0, "lid,B.L.001", 2210],
        [1, "lid.B.L.002", 2210],
        [0, "lid.B.L.002", 2207],
        [0, "lid.B.L.003", 2213],
        [1, "lid.T.L", 2213],
        [0, "lid.T.L", 2196],
        [0, "lid.T.L.001", 2193],
        [0, "lid.T.L.002", 2199],
    ]
    fvgroup = [
        "CenterBrow",
        "LipLowerMiddle",
        "LipUpperMiddle",
        "MidNoseBridge",
        "Nose",
        "lBrowInner",
        "lBrowMid",
        "lBrowOuter",
        "lCheekLower",
        "lCheekUpper",
        "lEar",
        "lEye",
        "lEyelidInner",
        "lEyelidLower",
        "lEyelidLowerInner",
        "lEyelidLowerOuter",
        "lEyelidOuter",
        "lEyelidUpper",
        "lEyelidUpperInner",
        "lEyelidUpperOuter",
        "lJawClench",
        "lLipCorner",
        "lLipUpperInner",
        "lLipUpperOuter",
        "lNasolabialLower",
        "lNasolabialMouthCorner",
        "lNostril",
        "lSquintInner",
        "lSquintOuter",
        "lowerJaw",
        "rBrowInner",
        "rBrowMid",
        "rBrowOuter",
        "rCheekLower",
        "rCheekUpper",
        "rEar",
        "rEye",
        "rEyelidInner",
        "rEyelidLower",
        "rEyelidLowerInner",
        "rEyelidLowerOuter",
        "rEyelidOuter",
        "rEyelidUpper",
        "rEyelidUpperInner",
        "rEyelidUpperOuter",
        "rJawClench",
        "rLipCorner",
        "rLipUpperInner",
        "rLipUpperOuter",
        "rNasolabialLower",
        "rNasolabialMouthCorner",
        "rNostril",
        "rSquintInner",
        "rSquintOuter",
        "tongue01",
        "tongue02",
        "tongue03",
        "upperJaw",
    ]

    fvgroup_swap = [
        ["ORG-teeth.T", "upperJaw"],
        ["ORG-teeth.B", "lowerJaw"],
        ["DEF-tongue.002", "tongue01"],
        ["DEF-tongue.001", "tongue02"],
        ["DEF-tongue", "tongue03"],
        ["DEF-cheek.T.L", "lSquintOuter"],
        ["DEF-cheek.T.L.001", "lSquintInner"],
        ["DEF-cheek.B.L.001", "lCheekUpper"],
        ["DEF-cheek.B.L", "lNasolabialMouthCorner"],
        # Chin
        ["DEF-chin", "Chin"],
        ["DEF-chin.001", "LipBelow"],
        ["DEF-jaw", "BelowJaw"],
        ["DEF-chin.L", "lNasolabialLower"],
        ["DEF-check.B.L", "lNasolabialMouthCorner"],
        ["DEF-cheek.B.L.001", "lCheekLower"],
        ["DEF-cheek.T.L", "lCheekUpper"],
        ["DEF-cheek.T.L.001", "lSquintInner"],
        ["DEF-jaw.L", "lJawClench"],
        ["DEF-brow.T.L.003", "lBrowInner"],
        ["DEF-brow.T.L.002", "lBrowMid"],
        ["DEF-brow.T.L.001", "lBrowOuter"],
        ["DEF-nose", "MidNoseBridge"],
        ["DEF-lid.T.L.003", "lEyelidUpperInner"],
        ["DEF-lid.T.L.002", "lEyelidUpper"],
        ["DEF-lid.T.L.001", "lEyelidUpperOuter"],
        ["DEF-lid.T.L", "lEyelidOuter"],
        ["DEF-nose.001", "Nose"],
        ["DEF-nose.L.001", "lLipBelowNose"],
        ["DEF-nose.L", "lNostril"],
        ["DEF-nose.004", "LipUpperMiddle"],
        ["ORG-eye.L", "lEye"],
        ["ear.L", "lEar"],
        # Lips
        ["DEF-lip.B.L.001", "lLipLowerOuter"],
        ["DEF-lip.B.L", "lLipLowerInner"],
        ["DEF-lip.T.L.001", "lLipUpperOuter"],
        ["DEF-lip.T.L", "lLipUpperInner"],
        ["DEF-forehead.L", "lCenterBrow"],
        ["DEF-forehead.R", "rCenterBrow"],
        ["DEF-lid.B.L.003", "lEyelidLowerOuter"],
        ["DEF-lid.B.L.002", "lEyelidLower"],
        ["DEF-lid.B.L.001", "lEyelidLowerInner"],
        ["DEF-lid.B.L", "lEyelidInner"],
    ]
    root_verts = [
        (0.7071067690849304, 0.7071067690849304, 0.0),
        (0.7071067690849304, -0.7071067690849304, 0.0),
        (-0.7071067690849304, 0.7071067690849304, 0.0),
        (-0.7071067690849304, -0.7071067690849304, 0.0),
        (0.8314696550369263, 0.5555701851844788, 0.0),
        (0.8314696550369263, -0.5555701851844788, 0.0),
        (-0.8314696550369263, 0.5555701851844788, 0.0),
        (-0.8314696550369263, -0.5555701851844788, 0.0),
        (0.9238795042037964, 0.3826834261417389, 0.0),
        (0.9238795042037964, -0.3826834261417389, 0.0),
        (-0.9238795042037964, 0.3826834261417389, 0.0),
        (-0.9238795042037964, -0.3826834261417389, 0.0),
        (0.9807852506637573, 0.19509035348892212, 0.0),
        (0.9807852506637573, -0.19509035348892212, 0.0),
        (-0.9807852506637573, 0.19509035348892212, 0.0),
        (-0.9807852506637573, -0.19509035348892212, 0.0),
        (0.19509197771549225, 0.9807849526405334, 0.0),
        (0.19509197771549225, -0.9807849526405334, 0.0),
        (-0.19509197771549225, 0.9807849526405334, 0.0),
        (-0.19509197771549225, -0.9807849526405334, 0.0),
        (0.3826850652694702, 0.9238788485527039, 0.0),
        (0.3826850652694702, -0.9238788485527039, 0.0),
        (-0.3826850652694702, 0.9238788485527039, 0.0),
        (-0.3826850652694702, -0.9238788485527039, 0.0),
        (0.5555717945098877, 0.8314685821533203, 0.0),
        (0.5555717945098877, -0.8314685821533203, 0.0),
        (-0.5555717945098877, 0.8314685821533203, 0.0),
        (-0.5555717945098877, -0.8314685821533203, 0.0),
        (0.19509197771549225, 1.2807848453521729, 0.0),
        (0.19509197771549225, -1.2807848453521729, 0.0),
        (-0.19509197771549225, 1.2807848453521729, 0.0),
        (-0.19509197771549225, -1.2807848453521729, 0.0),
        (1.280785322189331, 0.19509035348892212, 0.0),
        (1.280785322189331, -0.19509035348892212, 0.0),
        (-1.280785322189331, 0.19509035348892212, 0.0),
        (-1.280785322189331, -0.19509035348892212, 0.0),
        (0.3950919806957245, 1.2807848453521729, 0.0),
        (0.3950919806957245, -1.2807848453521729, 0.0),
        (-0.3950919806957245, 1.2807848453521729, 0.0),
        (-0.3950919806957245, -1.2807848453521729, 0.0),
        (1.280785322189331, 0.39509034156799316, 0.0),
        (1.280785322189331, -0.39509034156799316, 0.0),
        (-1.280785322189331, 0.39509034156799316, 0.0),
        (-1.280785322189331, -0.39509034156799316, 0.0),
        (0.0, 1.5807849168777466, 0.0),
        (0.0, -1.5807849168777466, 0.0),
        (1.5807852745056152, 0.0, 0.0),
        (-1.5807852745056152, 0.0, 0.0),
    ]

    eyelash = [
        "lEyelidInner",
        "lEyelidLower",
        "lEyelidLowerInner",
        "lEyelidLowerOuter",
        "lEyelidOuter",
        "lEyelidUpper",
        "lEyelidUpperInner",
        "lEyelidUpperOuter",
        "rEyelidInner",
        "rEyelidLower",
        "rEyelidLowerInner",
        "rEyelidLowerOuter",
        "rEyelidOuter",
        "rEyelidUpper",
        "rEyelidUpperInner",
        "rEyelidUpperOuter",
    ]

    # 1.DazGenitalA       (20200525)
    # 2.DazGenitalB
    # 3.G3(6,45)


f_geni = [
    [
        [0, 0],
        [2, 1],
        [24, 2],
        [30, 3],
        [35, 4],
        [48, 5],
        [50, 6],
        [168, 8],
        [927, 9],
        [1464, 10],
        [1718, 14],
        [1788, 16],
        [3308, 17],
        [3317, 19],
        [3548, 20],
        [3550, 21],
        [3552, 22],
        [4204, 25],
        [4662, 26],
        [4665, 27],
        [4699, 28],
        [5196, 35],
        [5198, 36],
        [6370, 38],
        [6678, 40],
        [7437, 41],
        [7974, 42],
        [8228, 46],
        [8298, 48],
        [9815, 50],
        [10040, 51],
        [10042, 52],
        [10687, 54],
        [11133, 55],
        [11169, 56],
        [11665, 63],
        [11667, 64],
        [12758, 66],
        [16556 + 1, 66],
        [20000, 0],
    ],
    [
        [0, 0],
        # [86, -18331],
        [87, 0],
        [377, 36],
        [378, 0],
        [1643, -16828],
        [1644, 0],
        [1893, -16544],
        [1894, 0],
        [2531, -15885],
        [2532, 0],
        [2533, -15880],
        [2534, 0],
        [2855, -15551],
        [2856, -15548],
        [2858, -15547],
        [2859, 0],
        [2860, -15542],
        [2861, 0],
        [4210, -14193],
        [4211, 0],
        [4465, -13928],
        [4466, 0],
        [4468, -13917],
        [4469, 0],
        [4476, -13925],
        [4477, 0],
        [8153, -9092],
        [8154, 0],
        [9365, -7819],
        [9366, -7816],
        [9367, 0],
        [9368, -7815],
        [9369, 0],
        [9370, -7810],
        [9371, 0],
        [10693, -6488],
        [10694, 0],
        [10955, -6224],
        [10956, 0],
        [11007, -6167],
        [11008, 0],
        [14716, -26],
        [14718, 0],
        [14742, 10],
        [14743, 0],
        [14785, -34],
        [14786, 0],
        [14804, -14],
        [14805, 0],
        [14848, -1],
        [14850, 0],
        [14863, -26],
        [14864, 0],
        [14928, -26],
        [14930, 0],
        [14954, 10],
        [14956, 0],
        [14981, -3],
        [14982, 0],
        [14983, 2],
        [14984, 0],
        [14994, -26],
        [14996, 0],
        [15049, 2],
        [15050, 0],
        [15114, 46],
        [15115, 0],
        [15520, -16],
        [15521, -26],
        [15522, 0],
        [15546, 10],
        [15547, 0],
        [15589, -34],
        [15590, 0],
        [15608, -14],
        [15609, 0],
        [15652, -1],
        [15654, 0],
        [15666, -26],
        [15667, 0],
        [15693, 26],
        [15694, 0],
        [15719, -2],
        [15720, 0],
        [15732, -26],
        [15734, 0],
        [15758, 10],
        [15759, 0],
        [15785, -3],
        [15786, 0],
        [15787, 2],
        [15788, 0],
        [15798, -26],
        [15800, 0],
        [15853, 2],
        [15854, 0],
        [16555, 0],
    ],
]
# 1.Daz GenitalA(20200525)
# 2.Daz GenitalB
# 3 G3
m_geni = [
    [
        [0, 0],
        [2, 1],
        [23, -16295],
        [24, 2],
        [29, -16290],
        [30, 3],
        [35, 4],
        [47, -16893],
        [48, 5],
        [49, -16335],
        [50, 6],
        [147, -16173],
        [148, 8],
        [874, -15447],
        [875, 9],
        [1410, -15385],
        [1411, 10],
        [1610, -15182],
        [1611, -14711],
        [1614, 14],
        [1684, 16],
        [3104, -13285],
        [3105, 17],
        [3114, -13226],
        [3116, 19],
        [3347, 20],
        [3349, 21],
        [3351, 22],
        [3979, 25],
        [4381, -12409],
        [4382, 26],
        [4385, 27],
        [4419, 28],
        [4909, -11418],
        [4910, -11887],
        [4911, -11417],
        [4916, 35],
        [4918, 36],
        [6064, -10321],
        [6065, -10322],
        [6066, 38],
        [6333, -9996],
        [6334, 40],
        [7060, -9270],
        [7061, 41],
        [7596, -9200],
        [7597, 42],
        [7796, -8997],
        [7797, -8534],
        [7800, 46],
        [7870, 48],
        [9288, -7053],
        [9290, 50],
        [9515, 51],
        [9517, 52],
        [10138, 54],
        [10530, -6261],
        [10531, 55],
        [10567, 56],
        [11056, -5280],
        [11057, -5741],
        [11058, -5279],
        [11063, 63],
        [11065, 64],
        [12130, -4256],
        [12131, -4257],
        [12132, 66],
        [16383, 66],
    ],
    [
        [0, 0],
        [2, 1],
        [36, 4],
        [50, 6],
        [291, 8],
        [927, 9],
        [1433, 10],
        [1998, 16],
        [2211, 15],
        [2213, 16],
        [3138, 19],
        [3385, 22],
        [4014, 25],
        [4428, 28],
        [4927, 36],
        [6071, 38],
        [6505, 40],
        [7081, 41],
        [7629, 42],
        [8157, 48],
        [9834, 52],
        [10277, 54],
        [10615, 56],
        [10650, 54],
        [10651, 56],
        [11074, 64],
        [12159, 66],
        [16384 + 1, 66],
        [20000, 0],
    ],
]


tbl_brollfix_g3_f = [
    ["-Hand", 87],
    ["-ForearmBend", 90],
    ["-ShldrBend", 90],
    ["-SmallToe1", -130 + 28],  # 0916
    ["-Index1", 30 + 40],
    ["-Mid1", 34 + 40],
    ["-Ring1", 33 + 40],
    ["-Pinky1", 28 + 40],
    ["-Index2", 30 + 40],
    ["-Mid2", 26 + 40],
    ["-Ring2", 33 + 40],
    ["-Pinky2", 35 + 40],
    ["-Index3", 31 + 40],
    ["-Mid3", 41 + 40],
    ["-Ring3", 40 + 40],
    ["-Pinky3", 33 + 40],
    ["-Thumb3", 50 + 40],
    ["-Thumb1", 45 + 40],
    ["-SmallToe4", 85],
    ["-SmallToe3", 68 + 10],
    ["-SmallToe2", 121],
    ["-BigToe", 84],
    ["-SmallToe4_2", 70 + 120],
    ["-SmallToe3_2", 117 - 100],
    ["-SmallToe2_2", 80 - 60],
    ["-SmallToe1_2", 80 - 60 + 19],
    ["-BigToe_2", 180 - 30],
]

tbl_brollfix = [
    ["-ForearmBend", 45],
    ["-ShldrBend", 43],
    ["-SmallToe1", -175],
    ["-Collar", 90],
    ["-Thumb3", 50],
    ["-Thumb2", 56],
    ["-Thumb1", 45],
    ["-Shin", 8],
    ["-Index1", 30],
    ["-ThighBend", 11],
    ["-Metatarsals", 56],
    ["-BigToe", -54],
    ["-Foot", 60],
    ["-BigToe_2", -140],
    # ['-Toe', 135],
    ["-Toe", 105],  # 290
    ["-Hand", 45],  # 290
    # ['-Hand', 40],
    ["-Index1", 30],
    ["-Mid1", 34],
    ["-Ring1", 33],
    ["-Pinky1", 28],
    ["-Index2", 30],
    ["-Mid2", 26],
    ["-Ring2", 33],
    ["-Pinky2", 35],
    ["-Index3", 31],
    ["-Mid3", 41],
    ["-Ring3", 40],
    ["-Pinky3", 33],
    ["-SmallToe4", 85],
    ["-SmallToe3", 68],
    ["-SmallToe2", 121],
    ["-BigToe", 84],
    ["-SmallToe4_2", 70],
    ["-SmallToe3_2", 117],
    ["-SmallToe2_2", 80],
    ["-SmallToe1_2", 80],
    ["-BigToe_2", 180],
]
mbone = [
    ["-Foot", 45],  # new290
    ["-Toe", 100],  # new290
    ["-Metatarsals", 80],
    ["-BigToe", 115],
    ["-BigToe_2", 180],
    ["-SmallToe1_2", 177],
    ["-SmallToe1", 105],
    ["-SmallToe2_2", 181],
    ["-SmallToe2", 102],
    ["-SmallToe3_2", 181],
    ["-SmallToe3", 88],
    ["-SmallToe4", 85],
    ["-SmallToe4_2", 187],
]

mbone_g3 = [
    ["-Foot", 18],  # new290
    ["-Toe", 100],  # new290
    ["-Metatarsals", 40],
    ["-BigToe", 100],
    ["-BigToe_2", 100],
    ["-SmallToe1_2", 45],
    ["-SmallToe1", 65],
    ["-SmallToe2_2", 82],
    ["-SmallToe2", 48],
    ["-SmallToe3_2", 53],
    ["-SmallToe3", 46],
    ["-SmallToe4", 27],
    ["-SmallToe4_2", 40],
]

daz_figure_list = [
    "Genesis9",
    "Genesis8Female",
    "Genesis8Male",
    "Genesis8_1Male",
    "Genesis8_1Female",
    "Genesis3Male",
    "Genesis3Female",
    "Genesis2Female",
    "Genesis2Male",
    "Genesis",
]

def get_figure_list():
    return daz_figure_list

g8_lower_extremity_bones_except_feet = ["hip", "pelvis", "lThighBend", "rThighBend", "lThighTwist", "rThighTwist", "lShin", "rShin"]
g9_lower_extremity_bones_except_feet = ["hip", "pelvis", "l_thigh", "r_thigh", "l_thightwist1", "l_thightwist2", "r_thightwist1", "r_thightwist2", "l_shin", "r_shin"]

def get_Lower_extremity_bones_except_feet():
    if Global.getIsG9():
        return g9_lower_extremity_bones_except_feet
    else:
        return g8_lower_extremity_bones_except_feet

def get_lower_extremities_to_flip():
    return g8_lower_extremity_bones_except_feet + g9_lower_extremity_bones_except_feet

# DB 2023-Mar-24: Genesis 8 to 9 bone lookup table
g8_to_g9_bones_dict = {
    'upperFaceRig': 'upperfacerig',
    'CenterBrow': 'centerbrow',
    'chestUpper': 'spine4',
    'neckLower': 'neck1',

    'lCollar': 'l_shoulder',
    'lThighBend': 'l_thigh',
    'lThighTwist': 'l_thightwist1',
    'lHand': 'l_hand',
    'lFoot': 'l_foot',
    'lShin': 'l_shin',
    'lEye': 'l_eye',

    'rCollar': 'r_shoulder',
    'rThighBend': 'r_thigh',
    'rThighTwist': 'r_thightwist1',
    'rHand': 'r_hand',
    'rFoot': 'r_foot',
    'rShin': 'r_shin',
    'rEye': 'r_eye',
}

def g8_to_9_bone(bonename_or_names):
    if isinstance(bonename_or_names, list):
        return [g8_to_9_bone(bonename) for bonename in bonename_or_names]
    else:
        search_name = bonename_or_names
        if search_name.endswith("_IK"):
            search_name = search_name[:-3]
        elif search_name.endswith("_P"):
            search_name = search_name[:-2]
        if search_name in g8_to_g9_bones_dict:
            new_bonename = g8_to_g9_bones_dict[search_name]
            if bonename_or_names.endswith("_IK"):
                new_bonename += "_IK"
            elif bonename_or_names.endswith("_P"):
                new_bonename += "_P"
            #print("DEBUG: renaming " + bonename_or_names + " to " + new_bonename)
            return new_bonename
        else:
            return bonename_or_names

def translate_bonenames(bonename_or_names):
    if Global.getIsG9():
        return g8_to_9_bone(bonename_or_names)
    else:
        return bonename_or_names
