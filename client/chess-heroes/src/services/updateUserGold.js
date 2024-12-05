import axios from 'axios'

const updateUserGold = async (user_id, access_token, amount) => {
    const axiosInstance = axios.create({
        httpsAgent: false,
        validateStatus: () => true
    })

    const response = await axiosInstance.put(
        `https://localhost:3000/user/player/gold/${user_id}`,
        {
            "amount": amount,
            "is_refill": true
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
    
    return response.data.new_balance
}

export default updateUserGold