from rest_framework import serializers
from .models import AuctionCase, AuctionItem, ClaimDistribution, AuctionParty, PropertyListing


class ClaimDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClaimDistribution
        fields = '__all__'

class AuctionPartySerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionParty
        fields = '__all__'

class PropertyListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyListing
        fields = '__all__'

class AuctionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuctionItem
        fields = '__all__'

class AuctionCaseSerializer(serializers.ModelSerializer):
    auctionitem_set = AuctionItemSerializer(many=True, read_only=True)
    claimdistribution_set = ClaimDistributionSerializer(many=True, read_only=True)
    auctionparty_set = AuctionPartySerializer(many=True, read_only=True)
    propertylisting_set = PropertyListingSerializer(many=True, read_only=True)

    class Meta:
        model = AuctionCase
        fields = '__all__'
