# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=255)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=150)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    id = models.BigAutoField(primary_key=True)
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


# 경매 사건 정보 (auction_data 초안5 (1).CSV)
class AuctionCase(models.Model):
    case_number = models.CharField(max_length=100, primary_key=True, help_text="사건번호")
    case_name = models.CharField(max_length=255, blank=True, null=True, help_text="사건명")
    court_name = models.CharField(max_length=255, blank=True, null=True, help_text="법원")
    filing_date = models.DateField(blank=True, null=True, help_text="접수일자")
    responsible_dept = models.CharField(max_length=255, blank=True, null=True, help_text="담당계")
    claim_amount = models.CharField(max_length=255, blank=True, null=True, help_text="청구금액")
    appeal_status = models.BooleanField(default=False, blank=True, null=True, help_text="항고여부")
    minimum_bid_price = models.CharField(max_length=255, blank=True, null=True, help_text="최저입찰가")
    
    # tender.html에서 사용되는 누락된 필드들
    case_status = models.CharField(max_length=50, blank=True, null=True, help_text="사건상태")
    final_result = models.CharField(max_length=100, blank=True, null=True, help_text="종국결과")
    final_date = models.DateField(blank=True, null=True, help_text="종국일자")

    class Meta:
        managed = True
        db_table = 'auction_case'

    def get_appeal_status_display(self):
        """항고여부 표시용"""
        return "항고" if self.appeal_status else "미항고"


# 배당 정보 (auction_data 초안5 (2).CSV)
class ClaimDistribution(models.Model):
    id = models.AutoField(primary_key=True)
    case_number = models.ForeignKey(AuctionCase, on_delete=models.CASCADE, to_field='case_number', db_column='case_number', help_text="사건번호") 
    location = models.TextField(blank=True, null=True, help_text="소재지")
    claim_deadline = models.DateField(blank=True, null=True, help_text="배당요구종기일")
    
    class Meta:
        managed = True
        db_table = 'claim_distribution'


# 물건 정보 (auction_data 초안5 (3).CSV)
class AuctionItem(models.Model):
    item_number = models.IntegerField(help_text="물건번호")
    case_number = models.ForeignKey(AuctionCase, on_delete=models.CASCADE, to_field='case_number', db_column='case_number', help_text="사건번호")
    property_name = models.CharField(max_length=255, blank=True, null=True, help_text="매물명(건물명)")
    item_spec_url = models.CharField(max_length=1000, blank=True, null=True, help_text="매각물건명세서URL")
    
    # 용도 및 주소 정보
    item_purpose = models.CharField(max_length=255, blank=True, null=True, help_text="물건용도")
    property_address = models.CharField(max_length=500, blank=True, null=True, help_text="매물주소")
    property_detail_address = models.CharField(max_length=200, blank=True, null=True, help_text="상세주소")
    floor_info = models.CharField(max_length=50, blank=True, null=True, help_text="층수정보")
    
    # 면적 정보
    building_area = models.CharField(max_length=100, blank=True, null=True, help_text="건물면적")
    
    # 기존 필드들
    valuation_amount = models.CharField(max_length=255, blank=True, null=True, help_text="감정평가액")
    item_note = models.CharField(max_length=255, blank=True, null=True, help_text="물건비고")
    item_status = models.CharField(max_length=255, blank=True, null=True, help_text="물건상태")
    auction_date = models.DateTimeField(blank=True, null=True, help_text="매각기일")
    auction_failures = models.IntegerField(default=0, blank=True, null=True, help_text="유찰횟수")
    item_image_url = models.URLField(blank=True, null=True, help_text="이미지URL")
    
    # tender.html에서 사용되는 추가 필드들
    property_type = models.CharField(max_length=100, blank=True, null=True, help_text="물건종류")
    deposit_amount = models.BigIntegerField(blank=True, null=True, help_text="입찰보증금")
    current_min_price = models.BigIntegerField(blank=True, null=True, help_text="현재 최저매각가격")
    
    class Meta:
        managed = True
        db_table = 'auction_item'
        unique_together = (('item_number', 'case_number'),)
    
    def __str__(self):
        return f"{self.case_number} - {self.property_name or '물건' + str(self.item_number)}"
    
    def get_formatted_address(self):
        """포맷된 주소 반환"""
        if self.property_address:
            address = self.property_address
            if self.building_name and self.building_name not in address:
                address += f" ({self.building_name})"
            if self.property_detail_address:
                address += f" {self.property_detail_address}"
            if self.floor_info:
                address += f" {self.floor_info}"
            return address
        return self.item_note or "주소 정보 없음"
    
    def get_area_info(self):
        """면적 정보 반환"""
        if self.area_info:
            return self.area_info
        
        areas = []
        if self.land_area:
            areas.append(f"토지: {self.land_area}")
        if self.building_area:
            areas.append(f"건물: {self.building_area}")
        return " / ".join(areas) if areas else None

    def calculate_deposit(self):
        """입찰보증금 계산 (현재 최저매각가격의 10%)"""
        if self.current_min_price:
            return int(self.current_min_price * 0.1)
        elif self.valuation_amount:
            try:
                val_amount = int(str(self.valuation_amount).replace(',', ''))
                return int(val_amount * 0.1)
            except (ValueError, TypeError):
                return 0
        return 0


# 매각기일 정보 추가
class AuctionSchedule(models.Model):
    id = models.AutoField(primary_key=True)
    auction_item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='schedules', help_text="물건정보")
    round_number = models.IntegerField(help_text="회차 (1차, 2차, 3차...)")
    auction_date = models.DateTimeField(blank=True, null=True, help_text="매각기일")
    decision_date = models.DateTimeField(blank=True, null=True, help_text="매각결정기일")
    minimum_price = models.BigIntegerField(blank=True, null=True, help_text="최저가격")
    result_status = models.CharField(max_length=50, blank=True, null=True, help_text="결과상태 (유찰/낙찰/기타)")
    
    # 추가 필드
    schedule_type = models.CharField(max_length=20, blank=True, null=True, help_text="기일 종류 (매각기일/매각결정기일/기타)")
    
    class Meta:
        managed = True
        db_table = 'auction_schedule'
        unique_together = (('auction_item', 'round_number'),)
        ordering = ['round_number']

class BuildingDetail(models.Model):
    auction_item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='building_details')
    sequence = models.IntegerField(default=1)  # 목록번호
    address = models.TextField(blank=True)  # 소재지
    building_type = models.CharField(max_length=50, default='집합건물')  # 목록구분
    building_details = models.TextField(blank=True)  # 상세내역
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['sequence']
        unique_together = ['auction_item', 'sequence']
    
    def __str__(self):
        return f"{self.auction_item.case_number.case_number} - 목록{self.sequence}"
    
    def get_details_lines(self):
        """상세내역을 줄 단위로 반환"""
        return self.building_details.split('\n') if self.building_details else []
# 목록 정보 (auction_data 초안5 (4).CSV)
class PropertyListing(models.Model):
    id = models.AutoField(primary_key=True)
    case_number = models.ForeignKey(AuctionCase, on_delete=models.CASCADE, to_field='case_number', db_column='case_number', help_text="사건번호")
    location = models.TextField(blank=True, null=True, help_text="소재지")
    listing_type = models.CharField(max_length=100, blank=True, null=True, help_text="목록구분")
    details = models.TextField(blank=True, null=True, help_text="상세내역")
    final_result = models.CharField(max_length=100, blank=True, null=True, help_text="종국결과")
    final_date = models.DateField(blank=True, null=True, help_text="종국일자")
    
    class Meta:
        managed = True
        db_table = 'property_listing'


# 당사자 정보 (auction_data 초안5 (5).CSV)
class AuctionParty(models.Model):
    id = models.AutoField(primary_key=True)
    case_number = models.ForeignKey(AuctionCase, on_delete=models.CASCADE, to_field='case_number', db_column='case_number', help_text="사건번호")
    party_type = models.CharField(max_length=100, blank=True, null=True, help_text="당사자구분")
    party_name = models.CharField(max_length=255, blank=True, null=True, help_text="당사자명")
    remarks = models.CharField(max_length=255, blank=True, null=True, help_text="비고")
    
    class Meta:
        managed = True
        db_table = 'auction_party'


# 물건 이미지 관리
class PropertyImage(models.Model):
    id = models.AutoField(primary_key=True)
    auction_item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='images', help_text="물건정보")
    image_url = models.URLField(help_text="이미지 URL")
    image_order = models.IntegerField(default=0, help_text="이미지 순서")
    is_main = models.BooleanField(default=False, help_text="메인 이미지 여부")
    description = models.CharField(max_length=200, blank=True, null=True, help_text="이미지 설명")
    
    class Meta:
        managed = True
        db_table = 'property_image'
        ordering = ['image_order']

# 문서 URL 관리
class PropertyDocument(models.Model):
    id = models.AutoField(primary_key=True)
    auction_item = models.OneToOneField(AuctionItem, on_delete=models.CASCADE, related_name='documents', help_text="물건정보")
    specification_url = models.URLField(blank=True, null=True, help_text="매각물건명세서 URL")
    appraisal_url = models.URLField(blank=True, null=True, help_text="감정평가서 URL")
    survey_url = models.URLField(blank=True, null=True, help_text="측량서 URL")
    register_url = models.URLField(blank=True, null=True, help_text="등기부등본 URL")
    
    class Meta:
        managed = True
        db_table = 'property_document'
