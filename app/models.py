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

    class Meta:
        managed = True
        db_table = 'auction_case'


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
    item_spec_url = models.CharField(max_length=1000, blank=True, null=True, help_text="매각물건명세서URL")
    item_purpose = models.CharField(max_length=255, blank=True, null=True, help_text="물건용도")
    valuation_amount = models.CharField(max_length=255, blank=True, null=True, help_text="감정평가액")
    item_note = models.CharField(max_length=255, blank=True, null=True, help_text="물건비고")
    item_status = models.CharField(max_length=255, blank=True, null=True, help_text="물건상태")
    auction_date = models.DateTimeField(blank=True, null=True, help_text="매각기일")
    auction_failures = models.IntegerField(default=0, blank=True, null=True, help_text="유찰횟수")
    item_image_url = models.URLField(blank=True, null=True, help_text="이미지URL")
    
    # 추가 매각기일 정보
    auction_date_1 = models.DateTimeField(blank=True, null=True, help_text="매각기일 1차")
    decision_date_1 = models.DateTimeField(blank=True, null=True, help_text="매각결정기일 1차")
    auction_date_2 = models.DateTimeField(blank=True, null=True, help_text="매각기일 2차")
    decision_date_2 = models.DateTimeField(blank=True, null=True, help_text="매각결정기일 2차")
    auction_date_3 = models.DateTimeField(blank=True, null=True, help_text="매각기일 3차")
    decision_date_3 = models.DateTimeField(blank=True, null=True, help_text="매각결정기일 3차")
    auction_date_4 = models.DateTimeField(blank=True, null=True, help_text="매각기일 4차")
    decision_date_4 = models.DateTimeField(blank=True, null=True, help_text="매각결정기일 4차")
    
    class Meta:
        managed = True
        db_table = 'auction_item'
        unique_together = (('item_number', 'case_number'),)


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
