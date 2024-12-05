import axios from 'axios'

const addBid = async (access_token, user_id, auction_id, amount) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.post(
        `https://localhost:3000/auction/bid/${auction_id}`,
        {
            "bidder_id": user_id,
            "bid_amount": amount
        },
        {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${access_token}`
            }
        }
    )
    
    if (response.status != 200) {
        throw new Error(response.data.err)  
    }
}

export default addBid